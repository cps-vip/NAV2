import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

import sys
import termios
import tty

def get_key(timeout=0.1):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

class WaypointPublisher(Node):

    def __init__(self):
        super().__init__('waypoint_publisher')
        self.publisher_ = self.create_publisher(PoseStamped, 'goal_pose', 10)        
        self.x = 7.0
        self.y = 8.0

    def check_move(self):
        key = get_key()

        if (key != None):
            pose = PoseStamped()
            pose.header.frame_id = "map"   # change to your TF frame
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = self.x
            pose.pose.position.y = self.y
            pose.pose.orientation.w = 1.0  # facing forward, no rotation

            self.publisher_.publish(pose)

        return



def main(args=None):
    rclpy.init(args=args)

    node = WaypointPublisher()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()