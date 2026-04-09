#include <chrono>
#include <memory>
#include <string>
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
    auto topic_callback =
      [this](geometry_msgs::msg::Twist msg) -> void {
        
        double linear_x = msg.linear.x;
        double angular_y = msg.angular.z;

        RCLCPP_INFO(this->get_logger(), "Linear x: %.2f, angular z: %.2f", linear_x, angular_y);
      };

    subscription_ =
      this->create_subscription<geometry_msgs::msg::Twist>("/cmd_vel", 10, topic_callback);
  }

private:
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<velocity_listener>());
  rclcpp::shutdown();
  return 0;
}