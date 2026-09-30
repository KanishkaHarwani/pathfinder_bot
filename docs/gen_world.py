import random

random.seed(7)  # same seed as the approved top-view image

# ---- Parameters ----
PATH_W = 2.0
WALL_T = 0.15
WALL_H = 0.75
N = 11

band_widths = []
for i in range(2 * N + 1):
    band_widths.append(WALL_T if i % 2 == 0 else PATH_W)
positions = [0]
for w in band_widths:
    positions.append(positions[-1] + w)
FOOTPRINT = positions[-1]

def cell_bounds(r, c):
    x0 = positions[2 * c + 1]
    x1 = positions[2 * c + 2]
    y0 = positions[2 * r + 1]
    y1 = positions[2 * r + 2]
    return x0, y0, x1, y1

DIRS = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

walls = {(r, c): {'N': True, 'S': True, 'E': True, 'W': True}
         for r in range(N) for c in range(N)}

center = N // 2
start = (center, center)
visited = {start}
stack = [start]
while stack:
    r, c = stack[-1]
    options = []
    for d, (dr, dc) in DIRS.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in visited:
            options.append((d, nr, nc))
    if options:
        d, nr, nc = random.choice(options)
        walls[(r, c)][d] = False
        walls[(nr, nc)][OPP[d]] = False
        visited.add((nr, nc))
        stack.append((nr, nc))
    else:
        stack.pop()

cx = FOOTPRINT / 2
cy = FOOTPRINT / 2
half = 1.5
open_x0, open_x1 = cx - half, cx + half
open_y0, open_y1 = cy - half, cy + half
CLEAR_MARGIN = 0.2

def overlaps_open(x0, y0, x1, y1):
    return not (x1 < open_x0 - CLEAR_MARGIN or x0 > open_x1 + CLEAR_MARGIN or
                y1 < open_y0 - CLEAR_MARGIN or y0 > open_y1 + CLEAR_MARGIN)

wall_rects = []

for i in range(N + 1):
    for j in range(N + 1):
        x0 = positions[2 * j]
        x1 = positions[2 * j] + WALL_T
        y0 = positions[2 * i]
        y1 = positions[2 * i] + WALL_T
        if not overlaps_open(x0, y0, x1, y1):
            wall_rects.append((x0, y0, x1, y1))

for r in range(N):
    for c in range(N):
        x0, y0, x1, y1 = cell_bounds(r, c)
        w = walls[(r, c)]
        if w['N']:
            seg = (x0, y0 - WALL_T, x1, y0)
            if not overlaps_open(*seg):
                wall_rects.append(seg)
        if w['S']:
            seg = (x0, y1, x1, y1 + WALL_T)
            if not overlaps_open(*seg):
                wall_rects.append(seg)
        if w['W']:
            seg = (x0 - WALL_T, y0, x0, y1)
            if not overlaps_open(*seg):
                wall_rects.append(seg)
        if w['E']:
            seg = (x1, y0, x1 + WALL_T, y1)
            if not overlaps_open(*seg):
                wall_rects.append(seg)

# shift so the maze (and the 3x3 spawn room) is centered on the world origin,
# matching where ros_gz_sim's spawn_entity places the robot by default
shift_x = -cx
shift_y = -cy

collisions = []
visuals = []
for idx, (x0, y0, x1, y1) in enumerate(wall_rects):
    dx = x1 - x0
    dy = y1 - y0
    px = (x0 + x1) / 2 + shift_x
    py = (y0 + y1) / 2 + shift_y
    pz = WALL_H / 2
    collisions.append(f'''        <collision name="wall_{idx}_collision">
          <pose>{px:.4f} {py:.4f} {pz:.4f} 0 0 0</pose>
          <geometry>
            <box>
              <size>{dx:.4f} {dy:.4f} {WALL_H}</size>
            </box>
          </geometry>
        </collision>''')
    visuals.append(f'''        <visual name="wall_{idx}_visual">
          <pose>{px:.4f} {py:.4f} {pz:.4f} 0 0 0</pose>
          <geometry>
            <box>
              <size>{dx:.4f} {dy:.4f} {WALL_H}</size>
            </box>
          </geometry>
          <material>
            <ambient>0.55 0.55 0.6 1</ambient>
            <diffuse>0.55 0.55 0.6 1</diffuse>
            <specular>0.3 0.3 0.3 1</specular>
          </material>
        </visual>''')

collisions_str = "\n".join(collisions)
visuals_str = "\n".join(visuals)

sdf = f'''<?xml version="1.0" ?>
<sdf version="1.9">
  <world name="default">

    <!-- As soon as a world defines ANY plugin, Gazebo stops auto-loading its
         defaults, so we have to explicitly list Physics/UserCommands/
         SceneBroadcaster (normally implicit) plus Sensors (never implicit,
         required for the camera and lidar to produce data) and Imu (never
         implicit either, required for the imu sensor to produce data). -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics">
    </plugin>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands">
    </plugin>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster">
    </plugin>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu">
    </plugin>

    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
      </attenuation>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>{FOOTPRINT + 2:.2f} {FOOTPRINT + 2:.2f}</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
            <specular>0.8 0.8 0.8 1</specular>
          </material>
        </visual>
      </link>
    </model>

    <!-- ============================================================ -->
    <!-- Maze walls - closed 11x11 grid, generated with a randomized   -->
    <!-- recursive-backtracker (a "perfect" maze: every cell reachable, -->
    <!-- no loops), plus a 3x3 open room at the exact center for the   -->
    <!-- robot to spawn in. Path width {PATH_W}m, wall thickness {WALL_T}m, wall  -->
    <!-- height {WALL_H}m. Footprint is {FOOTPRINT:.2f} x {FOOTPRINT:.2f}m (11 cells x 2.15m -->
    <!-- pitch is the closest fit to the requested 25 x 25m with an    -->
    <!-- odd cell count, so there's a true center cell). The whole     -->
    <!-- maze - and the spawn room - is centered on the world origin,  -->
    <!-- matching ros_gz_sim's default spawn pose. All geometry is     -->
    <!-- static (single link, {len(wall_rects)} box segments): regenerate with        -->
    <!-- gen_world.py (seed=7) if the layout ever needs to change.     -->
    <!-- ============================================================ -->
    <model name="maze">
      <static>true</static>
      <link name="walls">
{collisions_str}
{visuals_str}
      </link>
    </model>

  </world>
</sdf>
'''

with open('/home/claude/pathfinder_bot/maze.world', 'w') as f:
    f.write(sdf)

print("footprint:", FOOTPRINT)
print("wall segments:", len(wall_rects))
print("written to /home/claude/pathfinder_bot/maze.world")
