import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """
    Comprehensive launch file for co-simulation with NAV2.

    Brings up:
    1. Robot state publisher (RSP) - robot model
    2. Twist mux - velocity command multiplexing
    3. SLAM - simultaneous localization and mapping
    4. Gazebo - physics simulation (headless)
    5. Robot spawner - spawn robot in Gazebo
    6. ROS-Gazebo bridge - sensor/actuator communication
    7. Image bridge - camera topic bridging
    """

    package_name = "vipnav"

    # Robot state publisher - publishes robot URDF
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name), "launch", "rsp.launch.py"
                )
            ]
        ),
        launch_arguments={"use_sim_time": "true", "use_ros2_control": "false"}.items(),
    )

    #rviz2 - ros2 visualization. Look directly at ros2 topic.
    rviz2 = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rviz2.launch.py'
                )]))

    # Twist mux - multiplexes velocity commands from multiple sources
    twist_mux_params = os.path.join(
        get_package_share_directory(package_name), "config", "twist_mux.yaml"
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {"use_sim_time": True}],
        remappings=[("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")],
    )

    # SLAM - mapping and localization
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory(package_name),
                    "launch",
                    "slam.launch.py",
                )
            ]
        ),
        launch_arguments={
            "slam_params_file": os.path.join(
                get_package_share_directory(package_name),
                "config",
                "mapper_params_online_async_yaml",
            )
        }.items(),
    )

    # Gazebo simulator (headless mode)
    default_world = os.path.join(
        get_package_share_directory(package_name), "worlds", "obstacles.world"
    )

    world = LaunchConfiguration("world")
    headless = LaunchConfiguration("headless")

    world_arg = DeclareLaunchArgument(
        "world", default_value=default_world, description="World to load"
    )

    headless_arg = DeclareLaunchArgument(
        "headless", default_value="true", description="Run Gazebo in headless mode"
    )

    # Include the Gazebo launch file
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory("ros_gz_sim"),
                    "launch",
                    "gz_sim.launch.py",
                )
            ]
        ),
        launch_arguments={
            "headless": headless,
            "gz_args": ["-r -v4 ", world],
            "on_exit_shutdown": "true",
        }.items(),
    )

    waypoint_publisher = Node(
        package="vipnav",
        executable="waypoint_publisher.py"
    )

    # Robot spawner - spawn robot entity in Gazebo
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "my_bot", "-z", "0.1"],
        output="screen",
    )

    # ROS-Gazebo bridge - sensor/actuator communication
    bridge_params = os.path.join(
        get_package_share_directory(package_name), "config", "gz_bridge.yaml"
    )
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={bridge_params}",
        ],
    )

    # Image bridge - camera sensor bridging
    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"],
    )

    # Launch them all!
    return LaunchDescription(
        [
            world_arg,
            headless_arg,
            rsp,
            rviz2,
            twist_mux,
            slam,
            gazebo,
            waypoint_publisher,
            spawn_entity,
            ros_gz_bridge,
            ros_gz_image_bridge,
        ]
    )
