#!/bin/bash
# startup_laptop.sh - Laptop side of the distributed setup (v2).
# Runs: Gazebo sim + bridges, joystick, teleop, and RViz (navigation layout).
# Nav2 runs on the Jetson (see startup_jetson.sh).
#
# Start this first, wait for the robot to spawn, then start the Jetson.
# Requires: gnome-terminal. Layout: <ws>/src/pathfinder_bot/distributed/

DIST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$DIST_DIR/../../.." && pwd)"
SETUP_FILE="$WS_DIR/install/setup.bash"
PKG_DIR="$WS_DIR/src/pathfinder_bot"

if [ ! -f "$SETUP_FILE" ]; then
    echo "Could not find $SETUP_FILE. Build the workspace first (colcon build)."
    exit 1
fi

# Validate network.env before opening any tabs.
( source "$DIST_DIR/env_laptop.sh" ) || exit 1

PRE="source $DIST_DIR/env_laptop.sh && source $SETUP_FILE"

gnome-terminal --tab --title="Simulation" -- bash -c "$PRE; ros2 launch pathfinder_bot launch_sim.launch.py; exec bash"
sleep 5

gnome-terminal --tab --title="Joy Node" -- bash -c "$PRE; ros2 run joy joy_node --ros-args -p deadzone:=0.2; exec bash"
sleep 1

gnome-terminal --tab --title="Teleop Joy" -- bash -c "$PRE; ros2 run teleop_twist_joy teleop_node --ros-args -p axis_linear.x:=1 -p axis_angular.yaw:=0 -p scale_linear.x:=0.5 -p scale_angular.yaw:=1.0 -p enable_button:=0; exec bash"
sleep 1

# RViz alone: the map, costmaps and plans it shows come from the Jetson.
gnome-terminal --tab --title="RViz" -- bash -c "$PRE; rviz2 -d $PKG_DIR/rviz/pathfinder_nav.rviz --ros-args -p use_sim_time:=true; exec bash"
