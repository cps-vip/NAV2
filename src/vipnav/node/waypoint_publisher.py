#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import helics as h

SUBSTATION_MAP = {
    "Transformer_A": (2.0, -2.0),
    "Line_720": (2.0, 2.0),
    "Relay_1": (1.0, 2.0)
}

class BridgeNode(Node):
    def __init__(self):
        super().__init__('helics_bridge_node')
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('Bridge Node Started. Waiting for HELICS faults.')
    
    def send_goal(self, x, y):
        self.nav_to_pose_client.wait_for_server()
        
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.orientation.w = 1.0

        self.get_logger().info(f'Dispatching robot to fault at: x={x}, y={y}')
        
        # Track the goal acceptance and completion
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
        if status == 4: # 4 corresponds to SUCCEEDED
            self.get_logger().info('Arrived at fault location. Initiating sensor sweep...')
            # TODO: Trigger thermal camera logic here
        else:
            self.get_logger().error(f'Navigation failed. Status code: {status}')

def main(args=None):
    rclpy.init(args=args)
    node = BridgeNode()
    
    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
    h.helicsFederateInfoSetCoreInitString(fedinfo, "--federates=1")

    fed = h.helicsCreateValueFederate("Robot_Bridge_Fed", fedinfo)
    sub = h.helicsFederateRegisterSubscription(fed, "cc/fault_coordinates", "")
    h.helicsFederateEnterExecutingMode(fed)

    current_time = 0.0
    while h.helicsFederateGetState(fed) == h.HELICS_STATE_EXECUTION:
        if h.helicsInputIsUpdated(sub):
            fault_data = h.helicsInputGetString(sub)
            
            # Safely parse named components or raw coordinates
            if fault_data in SUBSTATION_MAP:
                x, y = SUBSTATION_MAP[fault_data]
                node.send_goal(x, y)
            else:
                try:
                    x, y = fault_data.split(',')
                    node.send_goal(x, y)
                except ValueError:
                    node.get_logger().error(f"Malformed HELICS payload: {fault_data}. Expected 'x,y' or known substation name.")
            
        current_time = h.helicsFederateRequestTime(fed, current_time + 3)
        rclpy.spin_once(node, timeout_sec=0.1)
    
    h.helicsFederateDisconnect(fed)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()