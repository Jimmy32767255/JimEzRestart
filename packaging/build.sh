#!/usr/bin/env bash
# Build a pacman-installable package from the working tree.
set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$here/.." && pwd)
pkgver=$(python3 -c 'import re, pathlib; print(re.search(r"__version__ = \"([^\"]+)\"", pathlib.Path("'"$repo"'/src/jimezrestart/__init__.py").read_text()).group(1))')
stage=$(mktemp -d "$repo/.build-stage.XXXXXX")
trap 'rm -rf "$stage"' EXIT

payload="$stage/jimezrestart-$pkgver"
mkdir -p "$payload/packaging"
cp -a "$repo/src" "$repo/data" "$repo/helper" "$repo/LICENSE" "$repo/README.md" "$payload/"
install -m755 "$repo/packaging/jimezrestart" "$payload/packaging/jimezrestart"
find "$payload" -type d -name __pycache__ -prune -exec rm -rf {} +

tar -C "$stage" -czf "$here/jimezrestart-$pkgver.tar.gz" "jimezrestart-$pkgver"

cd "$here"
makepkg --force --cleanbuild --nodeps
