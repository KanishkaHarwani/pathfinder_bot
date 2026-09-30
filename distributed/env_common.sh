# Shared by env_laptop.sh and env_jetson.sh. Source those, not this file.

pathfinder_env() {
    local role="$1"
    local dist_dir
    dist_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Tracked defaults (placeholders only).
    # shellcheck disable=SC1091
    source "$dist_dir/network.env"

    # Machine-specific values (not tracked by git) override the placeholders.
    if [ -f "$dist_dir/network.local.env" ]; then
        # shellcheck disable=SC1091
        source "$dist_dir/network.local.env"
    fi

    local ip_re='^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if ! [[ "$LAPTOP_IP" =~ $ip_re && "$JETSON_IP" =~ $ip_re ]]; then
        echo "LAPTOP_IP and JETSON_IP are not valid IPs."
        echo "Create $dist_dir/network.local.env (copy network.env) and set the real"
        echo "static IPs there. Do not put real IPs in the tracked network.env."
        return 1
    fi

    if [ "$role" = "laptop" ]; then
        export MY_IP="$LAPTOP_IP"
    else
        export MY_IP="$JETSON_IP"
    fi

    export PATHFINDER_ROLE="$role"
    export ROS_DOMAIN_ID
    export LAPTOP_IP JETSON_IP
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    export CYCLONEDDS_URI="file://$dist_dir/cyclonedds.xml"

    # Sim-time clock comes from Gazebo on the laptop via /clock.
    echo "[pathfinder] role=$role ip=$MY_IP domain=$ROS_DOMAIN_ID rmw=$RMW_IMPLEMENTATION"
}
