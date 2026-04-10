# CPS NAV2 IMPLEMENTATION

## How to run

Running NAV2 require 3 terminal: Core ROS2 sim launch, Waypoint_publisher, NAV2 navigation stack. Need to souce the package on each terminal

1. Launch the NAV2 stack
    - cd `~/NAV2/src`
    - `source install/setup.`
    - `ros2 launch vipnav navigation_launch.py use_sim_time:=True`
2. Launch the core Ros2 sim
    - cd `~/NAV2/src`
    - `source install/setup.`
    - `ros2 launch vipnav launch_sim.launch.py`
3. Run waypoint_publisher
    - cd `~/NAV2/src`
    - `source install/setup.`
    - `ros2 run vipnav waypoint_publisher.py`
  
## About

Core ROS2 sim contain the following module:
  1. Robot state publisher (RSP) - robot model
  2. Twist mux - velocity command multiplexing
  3. SLAM - simultaneous localization and mapping
  4. Gazebo - physics simulation (headless)
  5. Robot spawner - spawn robot in Gazebo
  6. ROS-Gazebo bridge - sensor/actuator communication
  7. Image bridge - camera topic bridging
  8. Rviz2 - Ros2 visualization

NAV2 Stack is the default NAV2 stack: https://docs.nav2.org/getting_started/index.html#

Waypoint_publisher:
1. Create a HELICS subscription Federate that listen to `cc/fault_coordinatinate`
2. Get input from the publication Federate, which should be coordinate value, and send to `navigate_to_pose` action server

# Mission 1 Implementation

Mission 1 demonstrates how a fault in a power grid simulation is detected and converted into a navigation task, where a robot autonomously moves to the fault location using NAV2.

The system connects:

- **GridLAB-D** → fault simulation
- **HELICS** → communication layer
- **ROS2 + Nav2** → robot navigation
- **Gazebo + RViz** → simulation and visualization

## Mission 1 Workflow

1. **Start HELICS Federates**
   - Transmission, Relay, and Control Center (CC) modules simulate the power grid system

2. **Fault Injection in GridLAB-D**
   - A fault is introduced in the grid simulation
   - This represents a failure in the system

3. **Fault Detection**
   - Relay and Control Center detect the fault and determine the fault location (coordinates)

4. **Send Coordinates via HELICS**
   - The fault location is sent through HELICS communication
   - It is received by the `waypoint_publisher` node

5. **Waypoint Publisher → Nav2**
   - The `waypoint_publisher` converts the coordinates and are sent as a navigation goal to Nav2

6. **Robot Navigation (Nav2)**
   - Nav2 computes a path and sends velocity commands which results in robot moves toward the target location in Gazebo

7. **Visualization in RViz**
   - Map, robot, and path are displayed
   - Green path shows planned trajectory

---

## System Architecture

![System Architecture Diagram](https://github.com/user-attachments/assets/80b08ca5-603b-450a-92d3-6c98ba40e999)

- GridLAB-D simulates the power line and injects faults into the system.
- HELICS acts as a communication broker that transfers data between the power system and ROS2.
- Gazebo simulates robot movement and environment physics.

---

## Initial Setup

On your computer's terminal run the following:

```bash
git clone https://github.com/elliotkantor/cosim-fault-injection.git
cd cosim-fault-injection
```

Open `Dockerfile` and add this block of code **before** `apt update` and save the file:

```dockerfile
RUN rm -f /usr/share/keyrings/ros-archive-keyring.gpg \
&& curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
 | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) \
signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
 http://packages.ros.org/ros2/ubuntu noble main" \
 > /etc/apt/sources.list.d/ros2.list
```

- Build the docker image using: `docker build -t cps_cosim .`
- Run container using: `docker run -d -p 8060:80 --name cps cps_cosim`
- Go to: [http://localhost:8060](http://localhost:8060)

---

## Setup Cosimulation Environment Inside Container

```bash
cd ~
git clone https://github.com/elliotkantor/cosim-fault-injection.git
cd cosim-fault-injection
python3 -m venv .venv
source .venv/bin/activate
pip install uv
uv sync
chmod +x install_software.sh
./install_software.sh
```

> Ignore any "not a git repository" error

---

## ROS2 Workspace Setup (New Terminal)

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/cps-vip/NAV2.git
git clone https://github.com/ros-teleop/twist_mux.git
```

Build the workspace:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --executor sequential
source install/setup.bash
```

---

## Terminal 1: Launch Simulation

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vipnav launch_sim.launch.py
```

*This starts Gazebo, RViz, Robot and its sensors.*

![Terminal 1 Launch Simulation Output](https://github.com/user-attachments/assets/2177e680-ef3c-4696-a056-9a7ce0ef3b92)
![Terminal 1 Launch Simulation Output](https://github.com/user-attachments/assets/66889a1b-6020-41fa-96ff-f00b2652a43f)


---

## Required RViz Displays

Add these displays in RViz:

| Display | Settings | Purpose |

|---------|----------|---------|
| Grid | Global Options → Fixed Frame: `map` | reference frame |
| RobotModel | Description Topic: `robot_description` | show robot |
| LaserScan | Topic: `/scan` | show lidar data |
| Map | Topic: `/map` | environment |
| Path | Topic: `/plan` | navigation path |

**This is how the Display pane in RViz should look after this step:**

![RViz Display Pane](https://github.com/user-attachments/assets/45d00d7b-9e39-45c4-9ed8-bcb4b2bd882a)
---

## Terminal 2: Launch NAV2

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch vipnav navigation_launch.py use_sim_time:=True
```

*This starts the navigation system (planner, controller, etc.). It enables path planning and movement.*

![Terminal 2 NAV2 Launch Output](https://github.com/user-attachments/assets/10133371-e33a-4533-8af6-6f2bea05e8c2)

---

## Terminal 3: Waypoint Publisher

```bash
cd ~/cosim-fault-injection
source .venv/bin/activate
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run vipnav waypoint_publisher.py
```

*This connects HELICS to robot.*

![Terminal 3 Waypoint Publisher Output](https://github.com/user-attachments/assets/2dd344c4-39e9-4213-9f06-6e6157471518)


---

## Terminal 4: Fault Injection

```bash
cd ~/software/cosim-fault-injection/simple_gridlabd_example
bash ./cc_run_example.sh
```

![Terminal 4 Fault Injection Output](https://github.com/user-attachments/assets/e0f58c0b-6724-4d03-b8e3-53aaf23598ca)


---

## Sending a Navigation Goal

1. Open RViz
2. Click **2D Pose Estimate**
3. Set the robot's starting position
4. Click **2D Goal Pose**
5. Click the target location on the map

### Expected Output

- Green path appears
- Robot moves toward goal in Gazebo and RViz

![RViz Navigation Path View](https://github.com/user-attachments/assets/faed963c-f7ee-4946-aebc-5b3e8c648979)


![Gazebo Robot Navigation View](https://github.com/user-attachments/assets/b7ca8f0f-3e13-484d-8862-ba9bf409374c)

---

## Troubleshooting

### Vipnav not found

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

### Build Issues

```bash
cd ~/ros2_ws
rm -rf build install log
source /opt/ros/jazzy/setup.bash
colcon build
```

### YAML error

```bash
pip install pyyaml
```

### Robot not moving in Gazebo Sim

**Step 1: Check if velocity commands are being published**

```bash
ros2 topic echo /cmd_vel
```

- If messages are being published → controller is working
- If no output → navigation stack may not be active

**Step 2: Check NAV2 lifecycle nodes**

```bash
ros2 lifecycle nodes
```

Check the state of important nodes:

```bash
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /behavior_server
```

Expected Output: `active [3]`

**Step 3: Activate nodes (if needed)**

```bash
ros2 lifecycle set /planner_server activate
ros2 lifecycle set /controller_server activate
ros2 lifecycle set /bt_navigator activate
ros2 lifecycle set /behavior_server activate
```

**Step 4: If activation fails**

```bash
ros2 lifecycle set /bt_navigator configure
ros2 lifecycle set /bt_navigator activate

ros2 lifecycle set /behavior_server configure
ros2 lifecycle set /behavior_server activate
```

**Step 5: Additional Checks**

- Ensure Gazebo is not paused
- Ensure Terminal 2 (navigation) is running
- Ensure 2D Pose Estimate is set before goal

### HELICS Error (broker not connected)

- Ensure `cc_run_example.sh` is running
- Restart all terminals if needed

### nav2_route missing

```bash
sudo apt update
sudo apt install ros-jazzy-nav2-route
```
