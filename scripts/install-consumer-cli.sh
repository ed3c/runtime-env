#!/bin/sh
set -eu

usage() {
  echo 'usage: install-consumer-cli.sh [--prefix ABSOLUTE_PATH]' >&2
  exit 64
}

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PREFIX=${HOME}/.local
if [ "$#" -gt 0 ]; then
  [ "$#" -eq 2 ] && [ "$1" = "--prefix" ] || usage
  PREFIX=$2
fi
case "$PREFIX" in
  /*) ;;
  *) echo 'FATAL: --prefix must be an absolute path' >&2; exit 64 ;;
esac

HEAD=$(git -C "$ROOT" rev-parse HEAD)
TREE=$(git -C "$ROOT" rev-parse 'HEAD^{tree}')
case "$HEAD:$TREE" in
  *[!0-9a-f:]*) echo 'FATAL: source revision is not a Git object id' >&2; exit 65 ;;
esac

VERSIONS="$PREFIX/lib/runtime-env"
DEST="$VERSIONS/$HEAD"
BIN="$PREFIX/bin"
LAUNCHER="$BIN/runtime-env"
mkdir -p "$VERSIONS" "$BIN"

if [ -e "$LAUNCHER" ] && ! grep -Fq '# managed-by: runtime-env/install-consumer-cli' "$LAUNCHER"; then
  echo "FATAL: refusing to replace unmanaged launcher: $LAUNCHER" >&2
  exit 73
fi

if [ ! -d "$DEST" ]; then
  TMP=$(mktemp -d "$VERSIONS/.install.XXXXXX")
  trap 'rm -rf "$TMP"' EXIT HUP INT TERM
  git -C "$ROOT" archive HEAD | tar -x -C "$TMP"
  python3 - "$TMP" "$TMP/INSTALL-RECEIPT.json" "$HEAD" "$TREE" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = Path(sys.argv[2])
commit, tree = sys.argv[3:]

def archive_sha256() -> str:
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if item == path or item.is_dir():
            continue
        relative = item.relative_to(root).as_posix().encode()
        content = (
            os.readlink(item).encode()
            if item.is_symlink()
            else item.read_bytes()
        )
        digest.update(relative + b"\0" + hashlib.sha256(content).digest())
    return digest.hexdigest()

with path.open("x", encoding="utf-8") as handle:
    json.dump(
        {
            "archive_sha256": archive_sha256(),
            "commit": commit,
            "schema": "runtime-env/consumer-cli-install/v1",
            "source": "committed-git-archive",
            "tree": tree,
        },
        handle,
        indent=2,
        sort_keys=True,
    )
    handle.write("\n")
os.chmod(path, 0o644)
PY
  chmod -R a-w "$TMP"
  mv "$TMP" "$DEST"
  trap - EXIT HUP INT TERM
fi

python3 - "$DEST" "$HEAD" "$TREE" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(sys.argv[1])
commit, tree = sys.argv[2:]
receipt_path = root / "INSTALL-RECEIPT.json"
try:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"FATAL: invalid installed revision receipt: {exc}")
digest = hashlib.sha256()
for item in sorted(root.rglob("*")):
    if item == receipt_path or item.is_dir():
        continue
    relative = item.relative_to(root).as_posix().encode()
    content = os.readlink(item).encode() if item.is_symlink() else item.read_bytes()
    digest.update(relative + b"\0" + hashlib.sha256(content).digest())
if (
    receipt.get("schema") != "runtime-env/consumer-cli-install/v1"
    or receipt.get("commit") != commit
    or receipt.get("tree") != tree
    or receipt.get("archive_sha256") != digest.hexdigest()
):
    raise SystemExit("FATAL: installed revision bytes do not match their receipt")
PY

LAUNCHER_TMP=$(mktemp "$BIN/.runtime-env.XXXXXX")
trap 'rm -f "$LAUNCHER_TMP"' EXIT HUP INT TERM
{
  echo '#!/bin/sh'
  echo '# managed-by: runtime-env/install-consumer-cli'
  echo 'set -eu'
  printf 'exec "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)/lib/runtime-env/%s/runtime-env" "$@"\n' "$HEAD"
} >"$LAUNCHER_TMP"
chmod 0755 "$LAUNCHER_TMP"
mv "$LAUNCHER_TMP" "$LAUNCHER"
trap - EXIT HUP INT TERM

echo "OK consumer CLI: commit=$HEAD launcher=$LAUNCHER"
