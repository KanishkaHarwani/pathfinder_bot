# Shared by env_laptop.sh and env_jetson.sh. Source those, not this file.

pathfinder_env() {
    local role="$1"
    local dist_dir
    dist_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # shellcheck disable=SC1091
    source "$dist_dir/network.env"

    local ip_re='^([0-9]{1,3}\.){3}[0-9]{1,3}$'
    if ! [[ "$LAPTOP_IP" =~ $ip_re && "$JETSON_IP" =~ $ip_re ]]; then
        echo "Set LAPTOP_IP and JETSON_IP in $dist_dir/network.env first."
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
