#!/bin/bash
# startup_jetson.sh - Jetson side of the distributed setup (v2).
# Runs Nav2 (map_server, AMCL, planner, controller, ...) without RViz.
# Works over SSH (no terminal tabs). Layout: <ws>/src/pathfinder_bot/distributed/
#
# Start the laptop first (startup_laptop.sh). This script waits for /clock
# from the simulation before starting Nav2.

DIST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$DIST_DIR/../../.." && pwd)"
SETUP_FILE="$WS_DIR/install/setup.bash"

if [ ! -f "$SETUP_FILE" ]; then
    echo "Could not find $SETUP_FILE. Build the workspace first (colcon build)."
    exit 1
fi

source "$DIST_DIR/env_jetson.sh" || exit 1
source "$SETUP_FILE"

echo "Waiting for /clock from the laptop (is the simulation running?)..."
for i in $(seq 1 30); do
    if timeout 3 ros2 topic echo --once /clock >/dev/null 2>&1; then
        echo "Got /clock. Starting Nav2."
        exec ros2 launch pathfinder_bot nav_bringup.launch.py rviz:=false
    fi
    echo "  still waiting ($i/30)"
done

echo "No /clock after ~90 s. Run ./check_link.sh for diagnostics."
exit 1
