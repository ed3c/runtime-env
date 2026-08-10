#!/usr/bin/env python3
"""Minimal Git credential fixture; never use outside runtime-env tests."""

from pathlib import Path
import os
import sys


state_root = Path(os.environ["FAKE_GIT_STATE_ROOT"])
mode = os.environ.get("FAKE_GIT_MODE", "normal")
state_root.mkdir(parents=True, exist_ok=True)
arguments = sys.argv[1:]
payload = sys.stdin.read()

if arguments[:2] == ["credential-osxkeychain", "store"]:
    path = state_root / "keychain"
    path.write_text(payload, encoding="utf-8")
    path.chmod(0o600)
elif arguments[:2] == ["credential-osxkeychain", "get"]:
    path = state_root / "keychain"
    if path.is_file():
        stored = "\n".join(
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("username=")
        ) + "\n"
        if mode == "keychain-mismatch":
            stored = "\n".join(
                "password=mismatch" if line.startswith("password=") else line
                for line in stored.splitlines()
            ) + "\n"
        sys.stdout.write(stored)
elif arguments and arguments[0] == "config":
    with (state_root / "config.log").open("a", encoding="utf-8") as handle:
        handle.write("\t".join(arguments[1:]) + "\n")
elif arguments and arguments[0] == "credential-store":
    action = arguments[-1]
    file_argument = next(
        (item for item in arguments if item.startswith("--file=")), None
    )
    if file_argument is None:
        raise SystemExit(64)
    store = Path(file_argument.split("=", 1)[1])
    if action == "erase":
        store.unlink(missing_ok=True)
    elif action == "get":
        if store.is_file():
            sys.stdout.write(store.read_text(encoding="utf-8"))
    else:
        raise SystemExit(64)
elif arguments[:2] == ["credential", "fill"]:
    path = state_root / "keychain"
    if not path.is_file():
        raise SystemExit(1)
    sys.stdout.write(path.read_text(encoding="utf-8"))
else:
    raise SystemExit(64)
