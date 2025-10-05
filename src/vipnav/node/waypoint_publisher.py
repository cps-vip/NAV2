#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose

import sys
import termios
import tty
import select
import threading

class WaypointNode(Node):
    def __init__(self):
        super().__init__('keyboard_node')
        self.get_logger().info('Keyboard node started. Press keys to see them. Press Ctrl+C to exit.')
        self.settings = termios.tcgetattr(sys.stdin)
        self.running = True
        self.thread = threading.Thread(target=self.keyboard_loop,daemon=True)
        self.thread.start()

        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.x = 1.0
        self.y = 1.0 

    def keyboard_loop(self):
        fd = sys.stdin.fileno()
        while self.running:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            key = sys.stdin.read(1).rstrip('\n') if rlist else None
            if key:
                self.get_logger().info(f'Key pressed: {repr(key)}')
                goal_msg = NavigateToPose.Goal()
                goal_msg.pose.header.frame_id = "map"
                goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
                goal_msg.pose.pose.position.x = self.x
                goal_msg.pose.pose.position.y = self.y
                goal_msg.pose.pose.orientation.w = 1.0

                
                self.get_logger().info(f'Sending goal: x={self.x}, y={self.y}')
                self.nav_to_pose_client.send_goal_async(goal_msg)


    def destroy_node(self):
        self.running = False 
        termios.tcsetattr(fd, termios.TCSADRAIN, self.settings)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    node = WaypointNode()

    rclpy.spin(node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()