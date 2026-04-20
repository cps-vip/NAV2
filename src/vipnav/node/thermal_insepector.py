#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
import cv2
from cv_bridge import CvBridge
import numpy as np

class ThermalInspector(Node):
    def __init__(self):
        super().__init__('thermal_inspector')
        self.bridge = CvBridge()
        
        self.subscription = self.create_subscription(
            Image,
            '/thermal_camera/image_raw',
            self.image_callback,
            10)
            
        self.marker_pub = self.create_publisher(Marker, '/fault_markers', 10)
        self.get_logger().info("Thermal Inspector Node Started.")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='mono8')
            
            _, thresholded = cv2.threshold(cv_image, 200, 255, cv2.THRESH_BINARY)
            
            contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 50:
                    self.get_logger().warn("HOTSPOT DETECTED in visual field!")
                    self.publish_rviz_marker()
                    
        except Exception as e:
            self.get_logger().error(f"Error processing thermal image: {e}")

    def publish_rviz_marker(self):
        marker = Marker()
        marker.header.frame_id = "base_link"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "thermal_faults"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        
        marker.pose.position.x = 1.0 
        marker.pose.position.y = 0.0
        marker.pose.position.z = 0.5
        
        marker.scale.x = 0.5
        marker.scale.y = 0.5
        marker.scale.z = 0.5
        marker.color.a = 0.8
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0

        self.marker_pub.publish(marker)

def main(args=None):
    rclpy.init(args=args)
    node = ThermalInspector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
