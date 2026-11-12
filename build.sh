#!/bin/bash
# Build a single-file quicktube binary into bin/.
#   ./build.sh           build with the local Python (needs python3-venv)
#   ./build.sh --docker  build in Debian bookworm, so the binary also runs on
#                        older systems (glibc 2.36 or newer). Use this for releases.
#   ./build.sh --windows build bin/quicktube.exe with Python under Wine in Docker.
# Only build/ and bin/quicktube are replaced. dist/, .venv and anything else
# in the folder are left alone.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
mkdir -p bin

if [ "${1:-}" = "--windows" ]; then
    echo "Building QuickTube.exe in Docker (tobix/pywine:3.13)..."
    docker run --rm -v "$PWD:/src:ro" -v "$PWD/bin:/out" tobix/pywine:3.13 sh -euc '
        cd /tmp
        wine python -m pip install -q -r /src/requirements.txt pyinstaller 2>/dev/null
        wine python -m PyInstaller --log-level WARN --noupx --onefile --collect-submodules rich._unicode_data --name quicktube --clean Z:/src/quicktube.py 2>&1 | grep -v "^[0-9a-f]*:\(fixme\|err\):" || true
        install -m 644 dist/quicktube.exe /out/quicktube.exe
        chown '"$(id -u):$(id -g)"' /out/quicktube.exe'
    echo "Done: bin/quicktube.exe ($(du -h bin/quicktube.exe | cut -f1))"
    exit 0
elif [ "${1:-}" = "--docker" ]; then
    echo "Building QuickTube in Docker (python:3.13-slim-bookworm)..."
    docker run --rm -v "$PWD:/src:ro" -v "$PWD/bin:/out" python:3.13-slim-bookworm sh -euc '
        apt-get update -qq && apt-get install -y -qq binutils >/dev/null
        pip install -q --root-user-action=ignore -r /src/requirements.txt pyinstaller
        cd /tmp && pyinstaller --log-level WARN --onefile --collect-submodules rich._unicode_data --name quicktube --clean /src/quicktube.py
        install -m 755 dist/quicktube /out/quicktube
        chown '"$(id -u):$(id -g)"' /out/quicktube'
else
    echo "Building QuickTube with the local Python..."
    [ -d .venv ] || python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt pyinstaller
    rm -rf build
    .venv/bin/pyinstaller --log-level WARN --onefile --collect-submodules rich._unicode_data --name quicktube --clean \
        --distpath build/dist --workpath build/work --specpath build quicktube.py
    install -m 755 build/dist/quicktube bin/quicktube
fi

echo "Done: bin/quicktube ($(bin/quicktube --version))"
