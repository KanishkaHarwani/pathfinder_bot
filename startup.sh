#!/bin/bash
# startup.sh - Launches the full Pathfinder Bot simulation stack
# (Gazebo sim, joystick input, teleop, and RViz) each in its own terminal tab.
#
# Requires: gnome-terminal (default on Ubuntu/GNOME desktops)
# Usage: ./startup.sh

WS_DIR=~/learn_ws
SETUP_FILE="$WS_DIR/install/setup.bash"

if [ ! -f "$SETUP_FILE" ]; then
    echo "Could not find $SETUP_FILE"
    echo "Update WS_DIR in this script to point to your ROS 2 workspace."
    exit 1
fi

# Terminal 1: Gazebo simulation + robot_state_publisher + bridges
gnome-terminal --tab --title="Simulation" -- bash -c "source $SETUP_FILE; ros2 launch pathfinder_bot launch_sim.launch.py; exec bash"
sleep 5

# Terminal 2: Joystick driver
# deadzone:=0.2 ignores axis input between -0.2 and 0.2 so no drift/noise
# gets sent downstream to teleop_twist_joy
gnome-terminal --tab --title="Joy Node" -- bash -c "source $SETUP_FILE; ros2 run joy joy_node --ros-args -p deadzone:=0.2; exec bash"
sleep 1

# Terminal 3: Joystick teleop -> cmd_vel
gnome-terminal --tab --title="Teleop Joy" -- bash -c "source $SETUP_FILE; ros2 run teleop_twist_joy teleop_node --ros-args -p axis_linear.x:=1 -p axis_angular.yaw:=0 -p scale_linear.x:=0.5 -p scale_angular.yaw:=1.0 -p enable_button:=0; exec bash"
sleep 1

# Terminal 4: RViz
gnome-terminal --tab --title="RViz" -- bash -c "source $SETUP_FILE; rviz2 -d $WS_DIR/src/pathfinder_bot/rviz/view_bot.rviz; exec bash"
