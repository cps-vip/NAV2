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
