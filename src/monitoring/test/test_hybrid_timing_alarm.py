from pathlib import Path
from importlib import import_module
from typing import Any, cast

from monitoring.latency_monitor_node import LatencyMonitorNode
from monitoring.topic_rate_monitor_node import TopicRateMonitorNode


_yaml = cast(Any, import_module('yaml'))


def _monitor_topics_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / 'config' / 'monitor_topics.yaml'
    return _yaml.safe_load(config_path.read_text(encoding='utf-8'))


def _thresholds_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / 'config' / 'thresholds.yaml'
    return _yaml.safe_load(config_path.read_text(encoding='utf-8'))


def _message_type_name(msg_type) -> str:
    assert msg_type is not None
    return msg_type.__name__


def test_hybrid_topics_have_expected_rates_per_robot():
    config = _monitor_topics_config()
    params = config['/monitoring/topic_rate_monitor_node']['ros__parameters']
    rate_by_topic = dict(zip(params['monitored_topics'], params['expected_rates_hz']))

    for robot_id in ('robot1', 'robot2', 'robot3'):
        assert rate_by_topic[f'/{robot_id}/camera/image_raw'] == 15.0
        assert rate_by_topic[f'/{robot_id}/fire_sensor_alert'] == 5.0
        assert rate_by_topic[f'/{robot_id}/fusion_decision'] == 2.0
        assert rate_by_topic[f'/{robot_id}/camera_detections'] == 5.0


def test_hybrid_latency_thresholds_are_configured():
    config = _thresholds_config()
    params = config['/monitoring/latency_monitor_node']['ros__parameters']

    assert params['camera_max_latency_ms'] == 200.0
    assert params['sensor_alert_max_latency_ms'] == 500.0


def test_monitor_nodes_infer_hybrid_message_types():
    assert _message_type_name(TopicRateMonitorNode._infer_msg_type('/robot1/camera/image_raw')) == 'Image'
    assert _message_type_name(TopicRateMonitorNode._infer_msg_type('/robot1/fire_sensor_alert')) == 'FireSensorAlert'
    assert _message_type_name(TopicRateMonitorNode._infer_msg_type('/robot1/fusion_decision')) == 'FusionDecision'
    assert _message_type_name(TopicRateMonitorNode._infer_msg_type('/robot1/camera_detections')) == 'VisionDetectionArray'

    assert _message_type_name(LatencyMonitorNode._infer_msg_type('/robot1/camera/image_raw')) == 'Image'
    assert _message_type_name(LatencyMonitorNode._infer_msg_type('/robot1/fire_sensor_alert')) == 'FireSensorAlert'
    assert _message_type_name(LatencyMonitorNode._infer_msg_type('/robot1/camera_detections')) == 'VisionDetectionArray'
