#!/bin/sh
set -eu
BLENDER_ROOT=/projects/tools/blender-local
export LD_LIBRARY_PATH="$BLENDER_ROOT/deps/extracted/usr/lib/x86_64-linux-gnu:$BLENDER_ROOT/runtime-libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$BLENDER_ROOT/blender-4.5.9-linux-x64/blender" --background --factory-startup --threads 2 --python /projects/work/living-town/art/production/build_panel_v3.py
