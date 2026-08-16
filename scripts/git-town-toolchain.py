#!/usr/bin/env python3
"""Manage one checksum-bound Git Town toolchain per user.

The manager is deliberately repository-agnostic. It installs only beneath a
user-owned runtime-env tool root and updates only a managed stable launcher.
Tests may provide an offline archive; live download is an explicit --download
transition against the exact immutable release URL from the checked-in manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "git-town-toolchain.json"
MANAGED_MARKER = ".runtime-env-git-town-managed"


class ToolchainError(ValueError):
    pass


def load_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolchainError(f"invalid manifest: {exc}") from exc
    if value.get("schema") != "runtime-env/git-town-toolchain-manifest/v1":
        raise ToolchainError("unsupported manifest schema")
    if value.get("tool") != "git-town":
        raise ToolchainError("manifest tool must be git-town")
    version = value.get("version")
    release = value.get("release")
    assets = value.get("assets")
    if not isinstance(version, str) or not version or version in {"latest", "main"}:
        raise ToolchainError("manifest version must be immutable")
    if not isinstance(release, dict) or release.get("tag") != f"v{version}" or release.get("immutable") is not True:
        raise ToolchainError("release tag/version/immutable identity mismatch")
    if release.get("repository") != "git-town/git-town":
        raise ToolchainError("unexpected upstream repository")
    if not isinstance(assets, dict) or not assets:
        raise ToolchainError("manifest assets missing")
    for key, asset in assets.items():
        if not isinstance(asset, dict) or set(asset) != {"name", "sha256"}:
            raise ToolchainError(f"invalid asset contract: {key}")
        if not isinstance(asset["name"], str) or not asset["name"].endswith(".tar.gz"):
            raise ToolchainError(f"invalid asset name: {key}")
        if not isinstance(asset["sha256"], str) or len(asset["sha256"]) != 64:
            raise ToolchainError(f"invalid asset digest: {key}")
    return value


def host_key(system: str | None = None, machine: str | None = None) -> str:
    sys_name = (system or platform.system()).lower()
    arch = (machine or platform.machine()).lower()
    systems = {"darwin": "darwin", "linux": "linux"}
    arches = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64", "amd64": "amd64"}
    if sys_name not in systems or arch not in arches:
        raise ToolchainError(f"unsupported platform/architecture: {sys_name}/{arch}")
    return f"{systems[sys_name]}-{arches[arch]}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def user_roots(tool_root: Path | None, launcher: Path | None) -> tuple[Path, Path]:
    home = Path.home().resolve()
    root = (tool_root or home / ".local" / "lib" / "runtime-env" / "git-town").expanduser().absolute()
    stable = (launcher or home / ".local" / "bin" / "git-town").expanduser().absolute()
    if ROOT.resolve() == root or ROOT.resolve() in root.parents:
        raise ToolchainError("repository-local tool installation is forbidden")
    return root, stable


def target_paths(manifest: dict, key: str, tool_root: Path) -> tuple[Path, Path, Path]:
    target = tool_root / manifest["version"] / key
    return target, target / "git-town", target / MANAGED_MARKER


def _download(manifest: dict, key: str, destination: Path) -> None:
    asset = manifest["assets"][key]
    url = f"https://github.com/git-town/git-town/releases/download/{manifest['release']['tag']}/{asset['name']}"
    with urlopen(url, timeout=60) as response, destination.open("wb") as output:  # noqa: S310 fixed origin
        shutil.copyfileobj(response, output)


def verify_archive(path: Path, manifest: dict, key: str) -> dict:
    asset = manifest["assets"].get(key)
    if asset is None:
        raise ToolchainError(f"manifest has no asset for {key}")
    observed = sha256(path)
    if observed != asset["sha256"]:
        raise ToolchainError(f"archive checksum mismatch for {asset['name']}")
    return {"asset": asset["name"], "sha256": observed, "platform": key}


def extract_binary(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with tarfile.open(archive, "r:gz") as tf:
            members = [m for m in tf.getmembers() if m.isfile() and Path(m.name).name == "git-town"]
            if len(members) != 1:
                raise ToolchainError("archive must contain exactly one git-town binary")
            member = members[0]
            member.name = "git-town"
            tf.extract(member, path=destination, filter="data")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    binary = destination / "git-town"
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def probe_version(binary: Path, expected: str) -> str:
    proc = subprocess.run([str(binary), "--version"], text=True, capture_output=True, check=False, timeout=15)
    if proc.returncode:
        raise ToolchainError(f"git-town --version exited {proc.returncode}")
    output = (proc.stdout + proc.stderr).strip()
    if expected not in output:
        raise ToolchainError(f"git-town version output does not contain {expected!r}")
    return output


def managed_launcher_target(launcher: Path, tool_root: Path) -> Path | None:
    if not launcher.exists() and not launcher.is_symlink():
        return None
    if not launcher.is_symlink():
        raise ToolchainError(f"refusing unmanaged launcher: {launcher}")
    target = launcher.resolve(strict=False)
    root = tool_root.resolve(strict=False)
    if root != target and root not in target.parents:
        raise ToolchainError(f"refusing launcher outside managed root: {launcher} -> {target}")
    return target


def build_receipt(manifest: dict, key: str, archive_meta: dict | None, binary: Path | None, launcher: Path, state: str, prior_target: Path | None) -> dict:
    return {
        "schema": "runtime-env/git-town-install-receipt/v1",
        "state": state,
        "manifest_sha256": hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "version": manifest["version"],
        "platform": key,
        "asset": archive_meta,
        "binary_sha256": sha256(binary) if binary and binary.is_file() else None,
        "launcher": str(launcher),
        "launcher_target": str(binary) if binary else None,
        "prior_managed_target": str(prior_target) if prior_target else None,
        "live_stack": "NOT_EXERCISED",
        "live_dual_forge": "NOT_EXERCISED",
    }


def write_receipt(path: Path | None, receipt: dict) -> None:
    if path is None:
        return
    path = path.expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ToolchainError(f"receipt already exists: {path}")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = path.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700:
        raise ToolchainError("receipt directory must be user-owned mode 0700")
    payload = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)


def plan(manifest: dict, key: str, tool_root: Path, launcher: Path) -> dict:
    target, binary, _ = target_paths(manifest, key, tool_root)
    prior = managed_launcher_target(launcher, tool_root)
    state = "INSTALLED" if binary.is_file() and prior == binary.resolve(strict=False) else "ABSENT"
    return build_receipt(manifest, key, None, binary if binary.is_file() else None, launcher, state, prior)


def apply(manifest: dict, key: str, tool_root: Path, launcher: Path, archive: Path | None, download: bool, receipt_path: Path | None) -> int:
    if os.geteuid() == 0 and os.environ.get("RUNTIME_ENV_ALLOW_TEST_ROOT") != "1":
        raise ToolchainError("refusing root/sudo installation")
    if archive is not None and download:
        raise ToolchainError("choose --archive or --download, not both")
    if archive is None and not download:
        raise ToolchainError("apply requires --archive or explicit --download")
    target, binary, marker = target_paths(manifest, key, tool_root)
    prior = managed_launcher_target(launcher, tool_root)
    tool_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    launcher.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary_archive: Path | None = None
    source = archive
    try:
        if download:
            fd, name = tempfile.mkstemp(prefix="git-town-", suffix=".tar.gz")
            os.close(fd)
            temporary_archive = Path(name)
            _download(manifest, key, temporary_archive)
            source = temporary_archive
        assert source is not None
        archive_meta = verify_archive(source, manifest, key)
        if target.exists():
            if not marker.is_file() or not binary.is_file():
                raise ToolchainError(f"existing unmanaged install target: {target}")
            probe_version(binary, manifest["version"])
        else:
            staging = target.parent / f".{target.name}.staging-{os.getpid()}"
            if staging.exists():
                shutil.rmtree(staging)
            extracted = extract_binary(source, staging)
            probe_version(extracted, manifest["version"])
            (staging / MANAGED_MARKER).write_text(json.dumps({"version": manifest["version"], "platform": key}) + "\n", encoding="utf-8")
            staging.rename(target)
        temporary_link = launcher.parent / f".{launcher.name}.tmp-{os.getpid()}"
        if temporary_link.exists() or temporary_link.is_symlink():
            temporary_link.unlink()
        temporary_link.symlink_to(binary)
        os.replace(temporary_link, launcher)
        observed = launcher.resolve(strict=True)
        if observed != binary.resolve(strict=True):
            raise ToolchainError("launcher readback mismatch")
        probe_version(observed, manifest["version"])
        receipt = build_receipt(manifest, key, archive_meta, binary, launcher, "PASS", prior)
        write_receipt(receipt_path, receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    finally:
        if temporary_archive is not None:
            temporary_archive.unlink(missing_ok=True)


def check(manifest: dict, key: str, tool_root: Path, launcher: Path, receipt_path: Path | None) -> int:
    target, binary, marker = target_paths(manifest, key, tool_root)
    try:
        prior = managed_launcher_target(launcher, tool_root)
    except ToolchainError as exc:
        receipt = build_receipt(manifest, key, None, None, launcher, "FAIL", None)
        receipt["reason"] = str(exc)
        print(json.dumps(receipt, sort_keys=True))
        return 2
    if not binary.is_file() or not marker.is_file() or prior != binary.resolve(strict=False):
        receipt = build_receipt(manifest, key, None, binary if binary.is_file() else None, launcher, "ABSENT", prior)
        write_receipt(receipt_path, receipt)
        print(json.dumps(receipt, sort_keys=True))
        return 3
    probe_version(binary, manifest["version"])
    receipt = build_receipt(manifest, key, None, binary, launcher, "PASS", prior)
    write_receipt(receipt_path, receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["plan", "check", "apply"])
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--platform", dest="platform_key")
    p.add_argument("--tool-root", type=Path)
    p.add_argument("--launcher", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--download", action="store_true")
    p.add_argument("--receipt", type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        key = args.platform_key or host_key()
        if key not in manifest["assets"]:
            raise ToolchainError(f"unsupported manifest platform: {key}")
        tool_root, launcher = user_roots(args.tool_root, args.launcher)
        if args.command == "plan":
            print(json.dumps(plan(manifest, key, tool_root, launcher), sort_keys=True))
            return 0
        if args.command == "check":
            return check(manifest, key, tool_root, launcher, args.receipt)
        return apply(manifest, key, tool_root, launcher, args.archive, args.download, args.receipt)
    except (ToolchainError, OSError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
