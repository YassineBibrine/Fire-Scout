#!/usr/bin/env python3

from __future__ import annotations

"""Lightweight lifecycle controller for slam_toolbox without bond monitoring.

The nav2_lifecycle_manager uses bond heartbeats to verify managed nodes are
responsive.  slam_toolbox (rclcpp_lifecycle::LifecycleNode base) does not
send bond heartbeats, so the nav2 manager immediately detects a heartbeat
timeout and tears down the stack.

This node replaces that manager: it transitions the node through its
lifecycle states (configure -> activate) via the standard lifecycle service
interface and periodically polls get_state for liveness, WITHOUT bond
involvement.
"""

import rclpy
from lifecycle_msgs.msg import Transition
from rclpy.timer import Timer as Timer
from lifecycle_msgs.srv import ChangeState, GetState
from rclpy.node import Node
from rclpy.task import Future


class SlamLifecycleController(Node):
    """Lifecycle controller for managing slam_toolbox nodes without bond."""

    def __init__(self) -> None:
        super().__init__("slam_lifecycle_controller")

        self.declare_parameter("robot_id", "robot1")
        self.declare_parameter("check_rate", 5.0)
        self._robot_id = self.get_parameter("robot_id").get_parameter_value().string_value
        self._check_rate = self.get_parameter("check_rate").get_parameter_value().double_value

        self._managed_node = f"slam_toolbox_{self._robot_id}"
        self._change_svc = f"/{self._managed_node}/change_state"
        self._get_state_svc = f"/{self._managed_node}/get_state"

        self._change_cli = self.create_client(ChangeState, self._change_svc)
        self._get_state_cli = self.create_client(GetState, self._get_state_svc)

        self._discovery_timer = self.create_timer(1.0, self._wait_for_services)
        self._activate_timer: Timer | None = None
        self._health_timer: Timer | None = None

        self.get_logger().info(
            f"SlamLifecycleController started for {self._managed_node}"
        )

    def _wait_for_services(self) -> None:
        """Wait until lifecycle services are available, then bring up the node."""
        if not self._change_cli.wait_for_service(timeout_sec=0.0):
            self.get_logger().info(
                f"Waiting for lifecycle services on {self._managed_node}..."
            )
            return

        self.get_logger().info(
            f"Lifecycle services ready for {self._managed_node}"
        )
        assert self._discovery_timer is not None
        self.destroy_timer(self._discovery_timer)
        self._discovery_timer = None

        self._send_transition(Transition.TRANSITION_CONFIGURE)

    def _send_transition(self, transition_id: int) -> None:
        """Send a lifecycle transition and attach a completion callback."""
        req = ChangeState.Request()
        req.transition.id = transition_id
        future = self._change_cli.call_async(req)
        future.add_done_callback(
            lambda f: self._on_transition_response(f, transition_id)
        )

    def _on_transition_response(self, future: Future, transition_id: int) -> None:
        """Handle the result of a lifecycle transition call."""
        try:
            response = future.result()
            assert response is not None
        except Exception as e:
            self.get_logger().error(f"Transition {transition_id} raised: {e}")
            return

        if not response.success:
            self.get_logger().warning(f"Transition {transition_id} reported failure (state may already be the target)")
            return

        self.get_logger().info(
            f"Transition {transition_id} succeeded for {self._managed_node}"
        )

        if transition_id == Transition.TRANSITION_CONFIGURE:
            self._activate_timer = self.create_timer(0.5, self._do_activate)
        elif transition_id == Transition.TRANSITION_ACTIVATE:
            self._health_timer = self.create_timer(self._check_rate, self._check_health)
            self.get_logger().info(
                f"Managed node {self._managed_node} is active"
            )

    def _do_activate(self) -> None:
        """Fire-once timer to send the activate transition."""
        assert self._activate_timer is not None
        self.destroy_timer(self._activate_timer)
        self._activate_timer = None
        self._send_transition(Transition.TRANSITION_ACTIVATE)

    def _check_health(self) -> None:
        """Poll get_state to see if the managed node is still responsive."""
        if not self._get_state_cli.service_is_ready():
            self.get_logger().warning(
                f"get_state service for {self._managed_node} is unavailable"
            )
            return

        future = self._get_state_cli.call_async(GetState.Request())
        future.add_done_callback(self._on_state_response)

    def _on_state_response(self, future: Future) -> None:
        """Log the current lifecycle state; report errors but do not kill."""
        try:
            response = future.result()
            assert response is not None
            current = response.current_state.id
            if current == 3:  # primary_state_ACTIVE
                return
            self.get_logger().warning(
                f"{self._managed_node} state is not ACTIVE (id={current})"
            )
        except Exception as e:
            self.get_logger().error(
                f"get_state failed for {self._managed_node}: {e}"
            )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SlamLifecycleController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
