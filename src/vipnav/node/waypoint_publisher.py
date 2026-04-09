#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
import helics as h
import time

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
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.orientation.w = 1.0

        self.get_logger().info(f'Dispatching to: x={x}, y={y}')

        self.nav_to_pose_client.wait_for_server()
        self.nav_to_pose_client.send_goal_async(goal_msg)


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
            fault_name = h.helicsInputGetString(sub)
            x, y = fault_name.split(',')
            node.send_goal(x, y)
            
        current_time = h.helicsFederateRequestTime(fed, current_time + 3)
        rclpy.spin_once(node, timeout_sec=0.1)
    
    h.helicsFederateDisconnect(fed)
    
    node.destroy_node()
    rclpy.shutdown()



if __name__ == '__main__':
    main()