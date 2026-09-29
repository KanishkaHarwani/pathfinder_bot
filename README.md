# Distributed setup (v2): simulation on a laptop, Nav2 on a Jetson

A reference setup for splitting Pathfinder across two machines. This is the setup the author uses, shared for anyone who wants to do something similar. It is **not a supported configuration**; expect to adapt it to your hardware and network.

For a single machine, ignore this folder and follow the main [README](../README.md).

## What runs where

| Laptop | Jetson |
|---|---|
| Gazebo, `ros_gz_bridge`, `ros_gz_image`, `robot_state_publisher` | `map_server`, AMCL, Nav2 (`nav_bringup.launch.py rviz:=false`) |
| RViz (`pathfinder_nav.rviz`) | |
| `joy_node`, `teleop_twist_joy` | |

Only lightweight topics cross the network (`/clock`, `/odom`, `/tf`, `/scan` one way; `/cmd_vel`, `/map`, costmaps, plans the other). Camera images and point clouds stay on the laptop. See [docs/Architecture.md](../docs/Architecture.md).

## Tested on

| | |
|---|---|
| Laptop | Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic |
| Jetson | Ubuntu 24.04, ROS 2 Jazzy: **fill in the model** |
| Link | Direct Ethernet with static IPs |
| DDS | Cyclone DDS (`rmw_cyclonedds_cpp`) |

## Setup

Do these once on each machine.

1. **Install ROS 2 Jazzy.**
   - Laptop: `ros-jazzy-desktop`, `ros-jazzy-ros-gz`, `ros-jazzy-rmw-cyclonedds-cpp`, plus `joy` and `teleop_twist_joy`.
   - Jetson: `ros-jazzy-navigation2`, `ros-jazzy-nav2-bringup`, `ros-jazzy-rmw-cyclonedds-cpp`.
2. **Clone and build the repo on both** (it is one package):
   ```bash
   cd ~/ros2_ws/src && git clone https://github.com/KanishkaHarwani/pathfinder_bot.git
   cd ~/ros2_ws
   rosdep install --from-paths src --ignore-src -r -y --skip-keys "ros_gz_sim ros_gz_bridge ros_gz_image"   # Jetson
   rosdep install --from-paths src --ignore-src -r -y                                                        # laptop
   colcon build --packages-select pathfinder_bot
   ```
   The Jetson needs the package because Nav2 reads its params and map from the package share directory. It never launches the sim.
3. **Set the addresses.** Edit `distributed/network.env` on **both** machines with the same values:
   ```bash
   export ROS_DOMAIN_ID=42
   export LAPTOP_IP=<laptop ethernet ip>
   export JETSON_IP=<jetson ethernet ip>
   ```
   Find each address with `ip -4 addr`. Both machines must be on the same subnet.

## Run

1. **Laptop:** `./distributed/startup_laptop.sh`. Wait until the robot has spawned in Gazebo.
2. **Jetson:** `./distributed/startup_jetson.sh`. It waits for `/clock` from the laptop, then starts Nav2.
3. In RViz on the laptop, the map and costmaps should appear. Send a **2D Goal Pose**.

## Verify the link

With both sides running, on each machine:

```bash
./distributed/check_link.sh laptop     # on the laptop
./distributed/check_link.sh jetson     # on the Jetson
```

It checks the ping, the simulation topics, the Nav2 topics, and that `/amcl`, `/bt_navigator` and `/robot_state_publisher` are visible from that machine.

## How discovery works

`cyclonedds.xml` disables multicast and lists both machines as peers, and binds DDS to the Ethernet address (`MY_IP`) so it never uses Wi-Fi. `env_laptop.sh` and `env_jetson.sh` set `ROS_DOMAIN_ID`, `RMW_IMPLEMENTATION` and `CYCLONEDDS_URI` and fill in the addresses from `network.env`. The startup scripts source them, so nothing depends on `~/.bashrc`.

To use the environment in your own terminals: `source distributed/env_laptop.sh` (or `env_jetson.sh`).

## Troubleshooting

| Symptom | Check |
|---|---|
| Ping works but the machines don't see each other's topics | Same `ROS_DOMAIN_ID` and `RMW_IMPLEMENTATION` on both? Did you `source` the env script in *that terminal*? Run `echo $CYCLONEDDS_URI`. |
| `ros2 topic list` shows nothing from the other side, ping fails | Wrong subnet or IP. Confirm both `ip -4 addr` outputs. |
| Firewall | `sudo ufw status`. If active, allow UDP between the two IPs (DDS uses UDP ports 7400 and up). |
| Nav2 starts but goals are rejected | Check `ros2 node list` from the Jetson for `/robot_state_publisher`. Run `check_link.sh` and look at which topic fails. |
| TF errors such as extrapolation into the past | Every Jetson node must use `use_sim_time:=true` (the default in `nav_bringup.launch.py`), and `/clock` must arrive. You may need to raise `transform_tolerance` in `config/nav2_params.yaml`. |
| Laggy RViz or dropped scans | Check the link speed with `ethtool <iface>`. Camera topics should not be shown on this setup. |

## Security note

There is no authentication or encryption on the ROS 2 link. This is fine on a private lab bench. Do not expose it to an untrusted network.
