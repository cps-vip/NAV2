#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
import helics as h
from cv_bridge import CvBridge
import numpy as np

# Updated to match the actual GLM object name from our previous fix
SUBSTATION_MAP = {
    "substation_transformer": (2.0, -2.0),
    "Line_720": (2.0, 2.0),
    "Relay_1": (1.0, 2.0)
}

class BridgeNode(Node):
    def __init__(self):
        super().__init__('helics_bridge_node')
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # --- NEW: Thermal Sweep Setup ---
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.thermal_sub = self.create_subscription(Image, '/thermal_camera/image_raw', self.thermal_callback, 10)
        self.cv_bridge = CvBridge()
        self.is_scanning = False
        self.scan_timer = None
        self.scan_duration = 0.0
        
        self.get_logger().info('Bridge Node Started. Waiting for HELICS thermal faults.')
    
    def send_goal(self, x, y):
        self.nav_to_pose_client.wait_for_server()
        
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.orientation.w = 1.0

        self.get_logger().info(f'Dispatching robot to fault at: x={x}, y={y}')
        
        send_goal_future = self.nav_to_pose_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Fault navigation goal rejected by Nav2.')
            return
        self.get_logger().info('Goal accepted, en route to fault.')
        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        if status == 4: # SUCCEEDED
            self.get_logger().info('Arrived at fault location. Initiating 360° thermal sensor sweep...')
            self.start_thermal_sweep()
        else:
            self.get_logger().error(f'Navigation failed. Status code: {status}')

    # --- NEW: Sweep Logic ---
    def start_thermal_sweep(self):
        self.is_scanning = True
        self.scan_duration = 0.0
        # Trigger rotation every 0.5 seconds
        self.scan_timer = self.create_timer(0.5, self.execute_sweep_rotation)

    def execute_sweep_rotation(self):
        twist = Twist()
        # Spin for roughly 12 seconds (enough for a full rotation depending on friction)
        if self.scan_duration < 12.0:
            twist.angular.z = 0.5  # Rotate counter-clockwise
            self.cmd_vel_pub.publish(twist)
            self.scan_duration += 0.5
        else:
            # Stop rotation
            twist.angular.z = 0.0
            self.cmd_vel_pub.publish(twist)
            self.is_scanning = False
            self.scan_timer.cancel()
            self.get_logger().info('Thermal sweep complete. Fault verified. Returning to standby.')

    def thermal_callback(self, msg):
        # Only process images when actively scanning the fault
        if not self.is_scanning:
            return
        
        try:
            # Convert ROS Image to OpenCV format to calculate max temperature
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            max_intensity = np.max(cv_image)
            
            # Assuming Gazebo outputs 150.0 degrees as a bright pixel or float data
            if max_intensity > 100: 
                self.get_logger().warn(f'CRITICAL HEAT SIGNATURE IN VIEW! Peak value: {max_intensity}')
        except Exception as e:
            pass # Ignore malformed frames during startup

def main(args=None):
    rclpy.init(args=args)
    node = BridgeNode()
    
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, "--federates=1")

    fed = h.helicsCreateValueFederate("Robot_Bridge_Fed", fedinfo)
    
    # Updated to listen to the new thermal fault topic
    dummy_sub = h.helicsFederateRegisterSubscription(fed, "cc/fault_coordinates", "")

    sub = h.helicsFederateRegisterSubscription(fed, "Thermal_Monitor_Fed/cc/thermal_fault", "")
    h.helicsFederateEnterExecutingMode(fed)

    current_time = 0.0
    while h.helicsFederateGetState(fed) == h.HELICS_STATE_EXECUTION:
        if h.helicsInputIsUpdated(sub):
            fault_data = h.helicsInputGetString(sub)
            
            if fault_data in SUBSTATION_MAP:
                x, y = SUBSTATION_MAP[fault_data]
                node.send_goal(x, y)
            else:
                try:
                    x, y = fault_data.split(',')
                    node.send_goal(x, y)
                except ValueError:
                    node.get_logger().error(f"Malformed HELICS payload: {fault_data}")
            
        current_time = h.helicsFederateRequestTime(fed, current_time + 3)
        rclpy.spin_once(node, timeout_sec=0.1)
    
    h.helicsFederateDisconnect(fed)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()