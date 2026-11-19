#!/bin/sh
set -eu
PANEL_PRODUCTION_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../art/production" && pwd)
BLENDER_ROOT=/projects/tools/blender-local
export LD_LIBRARY_PATH="$BLENDER_ROOT/deps/extracted/usr/lib/x86_64-linux-gnu:$BLENDER_ROOT/runtime-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$BLENDER_ROOT/blender-4.5.9-linux-x64/blender" --background --factory-startup --python-exit-code 1 --threads 1 --python "$PANEL_PRODUCTION_DIR/build_worker_v3.py" -- --direction "$1" --one-thread
