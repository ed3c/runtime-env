#!/usr/bin/env python3
"""Create a typed OpenShell provider without putting OAuth values in argv.

This is a one-time host bootstrap, not a workload entrypoint.  It reads a
carrier-owned credential file, passes only the required components through the
child process environment, and emits a content-free receipt.  The resulting
OpenShell provider is the runtime boundary; consumers receive its name, never
the source credential file or its values.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PROVIDER_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SAFE_CHILD_ENV = (
    "HOME",
    "LANG",
    "LC_ALL",
    "OPENSHELL_GATEWAY",
    "OPENSHELL_GATEWAY_ENDPOINT",
    "OPENSHELL_GATEWAY_INSECURE",
    "PATH",
    "SSL_CERT_FILE",
    "TMPDIR",
)
CODEX_COMPONENTS = {
    "access_token": "CODEX_AUTH_ACCESS_TOKEN",
    "refresh_token": "CODEX_AUTH_REFRESH_TOKEN",
    "account_id": "CODEX_AUTH_ACCOUNT_ID",
    "id_token": "CODEX_AUTH_ID_TOKEN",
}


class Refusal(Exception):
    """A fail-closed local input refusal."""


def private_regular_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise Refusal(f"credential source does not exist: {path}") from error
    if stat.S_ISLNK(metadata.st_mode):
        raise Refusal(f"credential source must not be a symlink: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        raise Refusal(f"credential source is not a regular file: {path}")
    if metadata.st_uid != os.getuid():
        raise Refusal(f"credential source is not owned by uid {os.getuid()}: {path}")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise Refusal(f"credential source must have mode 0600: {path}")


def read_codex_components(path: Path) -> dict[str, str]:
    private_regular_file(path)
    if path.stat().st_size > 1024 * 1024:
        raise Refusal("credential source exceeds the 1 MiB safety limit")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise Refusal("credential source is not valid UTF-8 JSON") from error
    if document.get("auth_mode") != "chatgpt":
        raise Refusal("Codex credential source must use auth_mode=chatgpt")
    tokens = document.get("tokens")
    if not isinstance(tokens, dict):
        raise Refusal("Codex credential source has no tokens object")

    values: dict[str, str] = {}
    for source_name, environment_name in CODEX_COMPONENTS.items():
        value = tokens.get(source_name)
        if source_name == "id_token" and value in (None, ""):
            continue
        if not isinstance(value, str) or not value:
            raise Refusal(f"Codex credential source is missing {source_name}")
        values[environment_name] = value
    return values


def write_receipt(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(document, stream, indent=2, sort_keys=True)
            stream.write("\n")
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def bootstrap_codex(
    name: str, auth_file: Path, receipt: Path, openshell_binary: Path
) -> None:
    components = read_codex_components(auth_file)
    child_environment = {
        key: os.environ[key] for key in SAFE_CHILD_ENV if key in os.environ
    }
    child_environment.update(components)
    command = [
        str(openshell_binary),
        "provider",
        "create",
        "--name",
        name,
        "--type",
        "codex",
    ]
    for variable in components:
        command.extend(("--credential", variable))
    try:
        completed = subprocess.run(
            command,
            env=child_environment,
            capture_output=True,
            text=False,
            check=False,
        )
    except OSError as error:
        raise Refusal(f"could not execute OpenShell: {error.strerror}") from error
    if completed.returncode != 0:
        raise Refusal(
            "OpenShell provider create failed with exit "
            f"{completed.returncode}; child output suppressed"
        )
    write_receipt(
        receipt,
        {
            "carrier": "codex-chatgpt",
            "credential_components": len(components),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "provider": name,
            "schema": "runtime-env/openshell-provider-receipt/v1",
            "status": "created",
        },
    )
    print(f"CREATED OpenShell provider {name}; credential values suppressed")
    print(f"RECEIPT {receipt}")


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Bootstrap a carrier-isolated OpenShell provider."
    )
    value.add_argument("carrier", choices=("codex-chatgpt",))
    value.add_argument("--name", required=True)
    value.add_argument("--auth-file", type=Path)
    value.add_argument("--openshell-bin", type=Path)
    value.add_argument("--receipt", required=True, type=Path)
    return value


def main(argv: list[str]) -> int:
    arguments = parser().parse_args(argv)
    if not PROVIDER_NAME.fullmatch(arguments.name):
        print("REFUSED: invalid provider name", file=sys.stderr)
        return 2
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    auth_file = arguments.auth_file or codex_home / "auth.json"
    discovered = arguments.openshell_bin or shutil.which("openshell")
    if discovered is None:
        print("REFUSED: openshell is not on PATH", file=sys.stderr)
        return 2
    openshell_binary = Path(discovered).expanduser().resolve()
    if not openshell_binary.is_file() or not os.access(openshell_binary, os.X_OK):
        print("REFUSED: OpenShell binary is not an executable file", file=sys.stderr)
        return 2
    try:
        bootstrap_codex(
            arguments.name, auth_file, arguments.receipt, openshell_binary
        )
    except Refusal as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
