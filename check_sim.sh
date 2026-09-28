#!/bin/bash
# check_sim.sh - Quick sanity check that the Pathfinder simulation is healthy.
#
# Usage: start the sim first (./startup.sh or
#        `ros2 launch pathfinder_bot launch_sim.launch.py`), then in another
#        terminal run: ./check_sim.sh
#
# Checks that each key topic publishes at least one message, then drives the
# robot forward briefly and confirms /odom changes.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
[ -f "$WS_DIR/install/setup.bash" ] && source "$WS_DIR/install/setup.bash"

if [ "$ROS_DISTRO" != "jazzy" ]; then
    echo "ROS_DISTRO is '${ROS_DISTRO:-unset}', expected jazzy. Source your workspace first."
    exit 1
fi

PASS=0
FAIL=0

check_topic() {
    local topic="$1"
    if timeout 10 ros2 topic echo --once "$topic" >/dev/null 2>&1; then
        echo "  [ OK ] $topic"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $topic (no message within 10 s)"
        FAIL=$((FAIL + 1))
    fi
}

echo "Publishing topics:"
for t in /clock /odom /tf /joint_states /imu /scan /scan/points \
         /camera/front/image /camera/front/depth_image \
         /camera/rear/image /camera/rear/depth_image; do
    check_topic "$t"
done

echo
echo "Drive test:"
get_x() {
    timeout 5 ros2 topic echo --once --field pose.pose.position.x /odom 2>/dev/null | head -1
}
X0="$(get_x)"
timeout 3 ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.3}}" >/dev/null 2>&1
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" >/dev/null 2>&1
sleep 1
X1="$(get_x)"

if [ -n "$X0" ] && [ -n "$X1" ] && \
   awk -v a="$X0" -v b="$X1" 'BEGIN { exit !((b - a > 0.2) || (a - b > 0.2)) }'; then
    echo "  [ OK ] odom x moved from $X0 to $X1"
    PASS=$((PASS + 1))
else
    echo "  [FAIL] odom did not change (x0='$X0', x1='$X1')"
    FAIL=$((FAIL + 1))
fi

echo
echo "Result: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
