#!/bin/bash
# check_link.sh - Verify the laptop <-> Jetson link. Run on either machine
# with the sim (laptop) and Nav2 (Jetson) running.

DIST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_DIR="$(cd "$DIST_DIR/../../.." && pwd)"

ROLE="$1"
if [ "$ROLE" != "laptop" ] && [ "$ROLE" != "jetson" ]; then
    echo "Usage: ./check_link.sh laptop|jetson   (the machine you are running this on)"
    exit 1
fi

source "$DIST_DIR/env_$ROLE.sh" || exit 1
[ -f "$WS_DIR/install/setup.bash" ] && source "$WS_DIR/install/setup.bash"

PASS=0; FAIL=0
ok()   { echo "  [ OK ] $1"; PASS=$((PASS + 1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }

PEER_IP="$JETSON_IP"; [ "$ROLE" = "jetson" ] && PEER_IP="$LAPTOP_IP"

echo "Network:"
if ping -c 2 -W 2 "$PEER_IP" >/dev/null 2>&1; then ok "ping $PEER_IP"; else fail "ping $PEER_IP"; fi
ip -4 addr | grep -q "inet $MY_IP/" && ok "this machine has $MY_IP" || fail "this machine does not have $MY_IP"

echo "Topics (from the simulation on the laptop):"
for t in /clock /odom /scan /tf; do
    if timeout 10 ros2 topic echo --once "$t" >/dev/null 2>&1; then ok "$t"; else fail "$t (no message in 10 s)"; fi
done

echo "Topics (from Nav2 on the Jetson):"
for t in /map /local_costmap/costmap; do
    if timeout 10 ros2 topic echo --once --qos-durability transient_local \
         --qos-reliability reliable "$t" >/dev/null 2>&1; then ok "$t"; else fail "$t (no message in 10 s)"; fi
done

echo "Nodes:"
NODES="$(ros2 node list 2>/dev/null)"
for n in /amcl /bt_navigator /robot_state_publisher; do
    echo "$NODES" | grep -qx "$n" && ok "$n visible" || fail "$n not visible"
done

echo
echo "Result: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
