#include <chrono>
#include <memory>
#include <string>
#include <iostream>

#include <fcntl.h>
#include <termios.h>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

/* This example creates a subclass of Node and uses a fancy C++11 lambda
* function to shorten the callback syntax, at the expense of making the
* code somewhat more difficult to understand at first glance. */

class velocity_listener : public rclcpp::Node
{
public:
  velocity_listener()
  : Node("velocity_listener")
  {
    serial_port = open("/dev/ttyAMA0", O_RDWR);

    if (serial_port < 0) {
      printf("Error %i from open: %s\n", errno, strerror(errno));
      return;
    }

    struct termios tty;

    tcgetattr(serial_port, &tty);
    cfsetispeed(&tty, B115200);

    auto topic_callback = [this](const geometry_msgs::msg::Twist msg) -> void {

        const double wheel_distance = 15.0;
        double linear_x = msg.linear.x;
        double angular_z = msg.angular.z;

        double right_velocity = linear_x + (wheel_distance * angular_z) / 2;
        double left_velocity = linear_x - (wheel_distance * angular_z) / 2;

        std::string data1 = "TR " + std::to_string(right_velocity) + "\n";
        std::string data2 = "TL " + std::to_string(left_velocity) + "\n";

        RCLCPP_INFO(this->get_logger(), "Linear x: %.2f, angular z: %.2f", linear_x, angular_z);

        write(serial_port, data1.c_str(), data1.size());
        write(serial_port, data2.c_str(), data2.size());
  };

    subscription_ =
      this->create_subscription<geometry_msgs::msg::Twist>(
        "/cmd_vel", 10, topic_callback);
  }
 
private: 
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr subscription_;
  int serial_port;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<velocity_listener>());
  rclcpp::shutdown();
  return 0;
}