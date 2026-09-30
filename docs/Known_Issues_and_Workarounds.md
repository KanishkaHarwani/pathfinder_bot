# Pathfinder Bot — Known Issues & Workarounds

Running log of bugs, gotchas, and non-obvious fixes hit during development. Check here before re-debugging something that might already be solved. Newest issues added at the bottom of each section as they're found.

---

## Simulation / Gazebo

### `nav2_bringup`'s TB3 demo launch fails: `package 'gazebo_ros' not found`
**Symptom:**
```
[ERROR] [launch]: Caught exception in launch: "package 'gazebo_ros' not found..."
```
**Cause:** `tb3_simulation_launch.py` targets **Gazebo Classic**, bridged via `gazebo_ros`. This project uses `ros_gz_sim`/`ros_gz_bridge` (Fortress, later Harmonic) — a different simulator and bridge stack entirely.

**Fix:** Not applicable to this project — don't chase it. Nav2 itself doesn't care which simulator produced the sensor data; it only needs `/scan`, `/tf`, `/odom`, which `gz_bridge.yaml` already provides. Use the project's own `launch_sim.launch.py`, not the TB3 demo, for any Nav2 testing.

### Migrating Fortress → Harmonic (Ubuntu 24.04 / ROS 2 Jazzy): old `ignition` plugin names silently stop working
**Symptom:** Diff drive and joint state publishing stop working after upgrading Gazebo, often with no obvious error — the robot just doesn't move or publish joint states.

**Cause:** Harmonic renamed the plugin libraries and namespaces. Fortress used `libignition-gazebo-diff-drive-system.so` / `ignition::gazebo::systems::DiffDrive`; Harmonic uses `gz-sim-diff-drive-system` / `gz::sim::systems::DiffDrive`. Same pattern for the joint state publisher plugin.

**Fix:** Update every `<plugin filename=... name=...>` tag in `gazebo_control.xacro` (and any world file with its own plugins) to the `gz-sim-*` / `gz::sim::systems::*` naming. Applied in `gazebo_control.xacro` this session.

### Migrating Fortress → Harmonic: lidar and RGBD cameras publish nothing, no error shown
**Symptom:** `/scan`, `/scan/points`, and the camera image/depth topics stay silent, but the sim otherwise runs fine and no error appears in the terminal.

**Cause:** The world's Sensors system plugin had `<render_engine>ogre</render_engine>`. Harmonic's `gpu_lidar` and `rgbd_camera` sensor types require the Ogre2 render path — `ogre` alone doesn't render what they need, and the failure is silent rather than a crash.

**Fix:** Change `<render_engine>ogre</render_engine>` to `<render_engine>ogre2</render_engine>` in the Sensors plugin block of the world file. Applied in `warehouse_world.sdf` this session.

### Migrating Fortress → Harmonic: `/imu` never publishes
**Symptom:** Every other sensor topic works; `/imu` has no publisher.

**Cause:** The world file had no IMU system plugin. This didn't matter under the old setup's plugin auto-loading behavior, but Harmonic needs it declared explicitly for `<sensor type="imu">` to actually produce data.

**Fix:** Add the IMU system plugin to the world file, alongside the other `gz-sim-*-system` plugins:
```xml
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
```
Applied in `warehouse_world.sdf` this session.

---

## SLAM (slam_toolbox)

### `Failed to compute odom pose` warnings, `/scan` messages dropped ("queue full")
**Symptom:**
```
[async_slam_toolbox_node-1] [WARN] ...: Failed to compute odom pose
[async_slam_toolbox_node-1] ...: Message Filter dropping message: ... queue is full
```
**Cause:** slam_toolbox's default `base_frame` param is `base_footprint`. This project's TF tree only has `base_link → chassis_link → ...` — there's no `base_footprint` anywhere in the URDF. slam_toolbox waits forever on a transform between `odom` and a frame that doesn't exist; incoming scans pile up in the message filter queue and get discarded.

**Fix:** Pass a params file overriding `base_frame: base_link`, e.g.:
```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true \
  slam_params_file:=<path>/config/mapper_params_online_async.yaml
```
See `config/mapper_params_online_async.yaml` in the repo for the full override file.

**Note (this session):** the same `base_footprint` vs `base_link` mismatch also affects Nav2 — see the Nav2 section below. Every base-frame parameter across both slam_toolbox and Nav2 needs the same fix.

### `slam_params_file` silently ignored, same errors as above persist
**Symptom:** Launch shows `[WARNING] [launch_ros.actions.node]: Parameter file path is not a file: ...yaml.` (note trailing period) and falls back to defaults.

**Cause:** Trailing punctuation accidentally copy-pasted into the path (e.g. a sentence's full stop swept in along with the command).

**Fix:** Always sanity-check the path before running: `ls <path-to-file>` should list it cleanly. Watch for trailing characters when copy-pasting commands out of chat, docs, or notes.

---

## Map viewing in RViz (map_server + RViz)

These issues were diagnosed in sequence during the original manual `map_server` testing, before Nav2 was wired in. **All of them are now moot for normal use** — Nav2's `bringup_launch.py` runs `map_server` and AMCL together and handles the lifecycle and `map` TF frame correctly. Kept here in case anyone runs `map_server` standalone again for debugging.

### 1. RViz Global Status: "Frame [map] does not exist"
**Cause:** `map_server` only stamps the OccupancyGrid *message* with `frame_id: map` in its header — it never broadcasts an actual `map` frame over `/tf` on its own. Normally `AMCL` (navigation) or `slam_toolbox` (mapping) publishes the live `map → odom` transform. Running `map_server` standalone, with neither active, nothing tells TF that `map` exists.

**Now resolved by:** AMCL, running as part of `nav_bringup.launch.py`, publishes `map → odom` continuously. No manual `static_transform_publisher` is needed anymore.

### 2. Map display still says "No map received" even with correct QoS and a valid `map` frame
**Cause:** A well-documented ROS 2 community issue reproduced identically on both Fast DDS and Cyclone DDS. `map_server` publishes `/map` with `TRANSIENT_LOCAL` durability exactly once, at activation. A subscriber (RViz) connecting after that single publish can miss it.

**Now resolved by:** running `map_server` through Nav2's lifecycle manager as designed; AMCL and normal Nav2 bringup don't hit the late-joiner problem the way ad hoc manual startup did.

### 3. Saved `pathfinder.rviz` has Fixed Frame set to `base_link`, breaking standalone map viewing
**Cause:** `base_link` is only a valid Fixed Frame when a live TF tree connects it to everything else.

**Now resolved by:** `rviz/pathfinder_nav.rviz` (new this session) is a separate config with Fixed Frame `map`, built specifically for viewing the map/costmaps/plan. `pathfinder.rviz` is kept as-is for close-up sensor/camera viewing with Fixed Frame `base_link`; use whichever config matches what you're looking at.

### 4. Saved camera view is zoomed too close to see a full map
**Cause:** `pathfinder.rviz`'s saved `Distance` was tuned for orbiting the robot model up close.

**Now resolved by:** `pathfinder_nav.rviz` uses a top-down orthographic view scaled for the full map instead of an orbit camera.

---

## Map alignment

### Map and robot/sensor readings don't line up after driving the robot post-mapping
**Cause:** With only the old placeholder `static_transform_publisher` running, `map == odom` was a fixed, permanent identity transform with no way to account for the robot having moved since the map was saved.

**Now resolved by:** AMCL, running as part of full Nav2 bringup, continuously re-publishes `map → odom` based on matching live lidar scans against the saved map, correcting for drift in real time.

---

## Nav2

### Goals rejected — "Action server is inactive. Rejecting the goal" — even though the map, costmaps, and AMCL particle cloud all look fine in RViz
**Symptom:**
```
[rviz2]: Setting goal pose: Frame:map, Position(...) ...
[bt_navigator]: Action server is inactive. Rejecting the goal.
```
No error appears near this line — the real cause is earlier in the log, from `lifecycle_manager_navigation` aborting bringup partway through.

**Cause:** `nav2_bringup`'s default managed-node list on this Jazzy install includes `docking_server` and `route_server`, in addition to the nodes this project's `nav2_params.yaml` originally covered (controller, planner, smoother, behavior, velocity smoother, collision monitor, bt_navigator, waypoint follower). `docking_server` has no config in a params file that predates it, fails to configure ("Charging dock plugins not given!"), and `lifecycle_manager_navigation` aborts the *entire* bringup sequence when any one of its managed nodes fails — so `bt_navigator` (which comes after it) never gets configured or activated, even though everything before it (including localization) came up fine.

**Fix:** Add a `docking_server` section to `config/nav2_params.yaml` with a placeholder/dummy dock plugin, even though this robot has no physical dock and the values are never actually used — it only needs to exist so the node can configure successfully:
```yaml
docking_server:
  ros__parameters:
    use_sim_time: true
    dock_plugins: ["simple_charging_dock"]
    simple_charging_dock:
      plugin: "opennav_docking::SimpleChargingDock"
      # ...
    docks: ["home_dock"]
    home_dock:
      type: "simple_charging_dock"
      frame: map
      pose: [0.0, 0.0, 0.0]
```
See the full block in `config/nav2_params.yaml`. Also add `error_code_names` under `bt_navigator` to silence a related (harmless but noisy) warning: `Error_code parameters were not set. Using default values of: follow_path_error_code compute_path_error_code`.

**How to diagnose this class of problem in general:** grep the launch output for `ERROR` and `Failed to bring up all requested nodes. Aborting bringup`, or check each managed node's lifecycle state directly:
```bash
for n in map_server amcl controller_server planner_server smoother_server \
         behavior_server velocity_smoother collision_monitor bt_navigator \
         waypoint_follower docking_server route_server; do
  echo -n "$n: "; ros2 lifecycle get /$n 2>&1 | head -1
done
```
The first node that isn't `active [3]` is where bringup actually stopped, regardless of which node's rejection message you happened to see in the logs. If Nav2 aborts on a node this project's `nav2_params.yaml` doesn't cover, compare against the installed default at `/opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml` — that node's default section is the fastest starting point.

### `base_footprint` vs `base_link` — same mismatch as slam_toolbox, but in Nav2's defaults
**Cause:** Nav2's default `nav2_params.yaml` assumes `base_footprint` as the robot base frame (AMCL, `bt_navigator`, both costmaps, behavior server, velocity smoother, collision monitor all reference it). This project's TF tree has no `base_footprint`.

**Fix:** Every one of those parameters is explicitly set to `base_link` in this project's `config/nav2_params.yaml`. If a future Nav2 default value gets added or an upgrade resets a param, check for `base_footprint` reappearing anywhere in the file.

### AMCL initial pose
**Not a bug, just a note:** `nav2_params.yaml` hardcodes AMCL's `initial_pose` to `(0, 0, 0)`, matching where the robot spawns and where the original map was recorded from. If the spawn point or map origin ever changes, either update `initial_pose` in the params file or set the pose manually each run with RViz's **2D Pose Estimate** tool.

---

## Joystick (Bluetooth controller, Ubuntu 24.04)

### Xbox Wireless Controller pairs and shows `Connected: yes` in `bluetoothctl`, but `joy_enumerate_devices` finds nothing and no `/dev/input/js0` appears
**Symptom:**
```
$ bluetoothctl info <MAC>
	Connected: yes
	Paired: yes
	Trusted: yes
$ ros2 run joy joy_enumerate_devices
(nothing listed)
$ ls /dev/input/js*
ls: cannot access '/dev/input/js*': No such file or directory
$ grep -A8 -i xbox /proc/bus/input/devices
(empty)
```
**Cause:** Being connected at the Bluetooth (RFCOMM/L2CAP) level is not the same as the kernel creating an input device for it. Two separate things were blocking that on this install:
1. The `uhid` kernel module (needed to turn a Bluetooth HID connection into a `/dev/input` device) wasn't loaded.
2. Bluetooth's ERTM (Enhanced Re-Transmission Mode) is known to break Xbox controllers specifically over Linux Bluetooth stacks.

Loading `uhid` and disabling ERTM together fixed it, but the fix didn't take effect on an already-connected controller — a disconnect/reconnect through `bluetoothctl` didn't help. A full power cycle of the controller (turning it off and back on) after making both changes was what actually got the input device to appear.

**Fix:**
```bash
sudo modprobe uhid
echo 1 | sudo tee /sys/module/bluetooth/parameters/disable_ertm
```
Then power-cycle the controller itself (not just disconnect/reconnect in software) and press the Xbox button to reconnect. Check:
```bash
ls /dev/input/js*
```
To make both changes survive a reboot:
```bash
echo uhid | sudo tee /etc/modules-load.d/uhid.conf
echo "options bluetooth disable_ertm=1" | sudo tee /etc/modprobe.d/bluetooth-ertm.conf
```
Also ensure `joydev` is loaded (creates the `js*` device node from the underlying input device) and persisted:
```bash
sudo modprobe joydev
echo joydev | sudo tee /etc/modules-load.d/joydev.conf
```
Confirm with `jstest /dev/input/js0`, then `ros2 run joy joy_enumerate_devices`.

**If this happens again after a reboot:** first check `cat /sys/module/bluetooth/parameters/disable_ertm` reads `Y` and `lsmod | grep -E "uhid|joydev"` shows both loaded — if the config files above didn't take effect for some reason (e.g. a kernel/initramfs quirk), reapply them manually and re-test before going further down this list.

**Diagnostic order used to isolate this** (useful for a different controller/adapter combo hitting a different link in the chain):
1. `lsusb` (wired only) / `bluetoothctl devices` — confirms hardware is seen at all
2. `bluetoothctl info <MAC>` — confirms Bluetooth-level connection
3. `grep -A8 -i <name> /proc/bus/input/devices` — confirms the kernel created an input device (empty output here is what pointed at `uhid`/ERTM rather than a `joy`/ROS problem)
4. `lsmod | grep joydev` + `sudo evtest` — confirms `joydev` and lets you watch raw input events even before `js0` exists
5. `ros2 run joy joy_enumerate_devices` — ROS-level check, last

### `ros-jazzy-joy` package layout differs from older ROS distros
**Note, not a bug:** `ros2 pkg executables joy` on Jazzy lists `game_controller_node`, `joy_enumerate_devices`, and `joy_node` — the `joy_enumerate_devices` and `game_controller_node` executables didn't exist under the Humble-era `joy` package used earlier in this project. `joy_enumerate_devices` in particular is useful as a first check (lists what SDL2 can see, independent of ROS topics) and was used to help isolate the Bluetooth issue above.

---

## Distributed setup (laptop + Jetson)

Not yet hit any issues in this category — the v2 distributed setup (`distributed/`) was built and tested working end to end this session on the first real attempt, using an explicit Cyclone DDS peer list (`distributed/cyclonedds.xml`) rather than multicast discovery, which was flagged as an open risk in the original architecture design. If problems come up on different hardware, log them here. See `distributed/README.md`'s troubleshooting table for the checks to run first (`check_link.sh`, matching `ROS_DOMAIN_ID`/`RMW_IMPLEMENTATION`, firewall/UDP, `use_sim_time` on every Jetson node).
