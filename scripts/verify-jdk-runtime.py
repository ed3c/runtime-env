#!/usr/bin/env python3
"""Verify a complete JDK without exposing its host path in command output."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile


VERSION = re.compile(r"\b(?:1\.)?(\d+)(?:\.\d+)*\b")
PROBE_CLASS = "RuntimeEnvJdkProbe"
PROBE_OUTPUT = "runtime-env-jdk-ok"


def command_version(executable: Path) -> int:
    result = subprocess.run(
        [str(executable), "-version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{executable.name} -version exited {result.returncode}")
    match = VERSION.search(f"{result.stdout}\n{result.stderr}")
    if match is None:
        raise RuntimeError(f"cannot parse {executable.name} feature release")
    return int(match.group(1))


def verify(jdk_home: Path, expected_feature: int) -> None:
    java = jdk_home / "bin" / "java"
    javac = jdk_home / "bin" / "javac"
    for executable in (java, javac):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise RuntimeError(f"JDK is incomplete: missing executable bin/{executable.name}")

    java_feature = command_version(java)
    javac_feature = command_version(javac)
    if java_feature != expected_feature or javac_feature != expected_feature:
        raise RuntimeError(
            "JDK feature mismatch: "
            f"expected={expected_feature} java={java_feature} javac={javac_feature}"
        )

    with tempfile.TemporaryDirectory(prefix="runtime-env-jdk-") as scratch:
        directory = Path(scratch)
        source = directory / f"{PROBE_CLASS}.java"
        source.write_text(
            "public final class RuntimeEnvJdkProbe {"
            ' public static void main(String[] args) { System.out.print("runtime-env-jdk-ok"); }'
            " }\n",
            encoding="utf-8",
        )
        compiled = subprocess.run(
            [str(javac), "-d", str(directory), str(source)],
            check=False,
            capture_output=True,
            timeout=30,
        )
        if compiled.returncode != 0 or not (directory / f"{PROBE_CLASS}.class").is_file():
            raise RuntimeError(f"javac compile probe exited {compiled.returncode}")
        executed = subprocess.run(
            [str(java), "-cp", str(directory), PROBE_CLASS],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if executed.returncode != 0 or executed.stdout != PROBE_OUTPUT:
            raise RuntimeError(f"java execution probe exited {executed.returncode}")

    print(
        f"JDK-RUNTIME GREEN java={java_feature} javac={javac_feature} compile-run=passed"
    )


def selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="runtime-env-jdk-selftest-") as scratch:
        home = Path(scratch)
        bin_directory = home / "bin"
        bin_directory.mkdir()
        java = bin_directory / "java"
        javac = bin_directory / "javac"
        java.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = -version ]; then echo 'openjdk version \"21.0.8\"' >&2; exit 0; fi\n"
            f"printf '%s' '{PROBE_OUTPUT}'\n",
            encoding="utf-8",
        )
        javac.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = -version ]; then echo 'javac 21.0.8'; exit 0; fi\n"
            "shift; out=$1; touch \"$out/RuntimeEnvJdkProbe.class\"\n",
            encoding="utf-8",
        )
        java.chmod(0o700)
        javac.chmod(0o700)
        verify(home, 21)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    raw_home = os.environ.get("JAVA_HOME")
    if not raw_home:
        raise SystemExit("MISSING required environment: JAVA_HOME")
    raw_feature = os.environ.get("JAVA_VERSION", "21")
    if not raw_feature.isdigit():
        raise SystemExit("INVALID JAVA_VERSION: expected a decimal feature release")
    try:
        verify(Path(raw_home).expanduser().resolve(), int(raw_feature))
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"JDK-RUNTIME RED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
