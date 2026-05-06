from pathlib import Path

import xml.etree.ElementTree as ET


def test_robot_lidar_uses_gazebo_ionic_sensor_shape():
    model_path = Path(__file__).resolve().parents[1] / 'models' / 'model.sdf'
    root = ET.fromstring(model_path.read_text(encoding='utf-8').lstrip())

    lidar = root.find(".//sensor[@name='lidar']")
    assert lidar is not None
    assert lidar.attrib.get('type') == 'gpu_lidar'

    topic = lidar.findtext('topic')
    assert topic == '~/lidar'

    assert lidar.find('lidar') is not None
    assert lidar.find('ray') is None
    assert lidar.findtext('visualize') == 'true'
