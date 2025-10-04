#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

import sys
import termios
import tty
import select
import threading

class KeyboardNode(Node):
    def __init__(self):
        super().__init__('keyboard_node')
        self.get_logger().info('Keyboard node started. Press keys to see them. Press Ctrl+C to exit.')
        self.settings = termios.tcgetattr(sys.stdin)
        self.running = True
        self.thread = threading.Thread(target=self.keyboard_loop,daemon=True)
        self.thread.start()

    def keyboard_loop(self):
        fd = sys.stdin.fileno()
        while self.running:
            rlist, _, _ = select.select([sys.stdin], [], [], 0.0)
            key = sys.stdin.read(1) if rlist else None
            self.get_logger().info(f'Key pressed: {repr(key)}') if key else None

    def destroy_node(self):
        self.running = False 
        termios.tcsetattr(fd, termios.TCSADRAIN, self.settings)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    node = KeyboardNode()

    rclpy.spin(node)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()