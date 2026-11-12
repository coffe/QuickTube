#!/bin/bash
# Build a single-file quicktube binary into bin/.
#   ./build.sh           build with the local Python (needs python3-venv)
#   ./build.sh --docker  build in Debian bookworm, so the binary also runs on
#                        older systems (glibc 2.36 or newer). Use this for releases.
# Only build/ and bin/quicktube are replaced. dist/, .venv and anything else
# in the folder are left alone.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
mkdir -p bin

if [ "${1:-}" = "--docker" ]; then
    echo "Building QuickTube in Docker (python:3.13-slim-bookworm)..."
    docker run --rm -v "$PWD:/src:ro" -v "$PWD/bin:/out" python:3.13-slim-bookworm sh -euc '
        apt-get update -qq && apt-get install -y -qq binutils >/dev/null
        pip install -q --root-user-action=ignore -r /src/requirements.txt pyinstaller
        cd /tmp && pyinstaller --log-level WARN --onefile --name quicktube --clean /src/quicktube.py
        install -m 755 dist/quicktube /out/quicktube
        chown '"$(id -u):$(id -g)"' /out/quicktube'
else
    echo "Building QuickTube with the local Python..."
    [ -d .venv ] || python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt pyinstaller
    rm -rf build
    .venv/bin/pyinstaller --log-level WARN --onefile --name quicktube --clean \
        --distpath build/dist --workpath build/work --specpath build quicktube.py
    install -m 755 build/dist/quicktube bin/quicktube
fi

echo "Done: bin/quicktube ($(bin/quicktube --version))"
