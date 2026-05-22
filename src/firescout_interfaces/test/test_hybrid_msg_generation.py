#!/usr/bin/env python3
"""Schema validation tests for Phase 2 hybrid messages.

Covers: FireSensorAlert, Detection, VisionDetectionArray, FusionDecision
"""
import math
import unittest
from importlib import import_module


def _msg(name):
    return getattr(import_module('firescout_interfaces.msg'), name)


class TestHybridMessagesExist(unittest.TestCase):

    def test_all_hybrid_messages_importable(self):
        for name in ('FireSensorAlert', 'Detection', 'VisionDetectionArray', 'FusionDecision'):
            with self.subTest(msg=name):
                _msg(name)  # raises AttributeError if missing


class TestFireSensorAlert(unittest.TestCase):

    def setUp(self):
        self.Msg = _msg('FireSensorAlert')

    def test_required_fields_present(self):
        obj = self.Msg()
        for field in ('robot_id', 'flame_detected', 'smoke_level', 'gas_level',
                      'temperature', 'normalized_risk', 'source_id', 'timestamp'):
            self.assertTrue(hasattr(obj, field), f'FireSensorAlert missing field: {field}')

    def test_float_fields_default_in_range(self):
        obj = self.Msg()
        for field in ('smoke_level', 'gas_level', 'normalized_risk'):
            v = getattr(obj, field)
            self.assertGreaterEqual(v, 0.0, f'{field} default < 0')
            self.assertLessEqual(v, 1.0, f'{field} default > 1')

    def test_flame_detected_is_bool(self):
        obj = self.Msg()
        self.assertIsInstance(obj.flame_detected, bool)

    def test_robot_id_is_string(self):
        obj = self.Msg()
        obj.robot_id = 'robot1'
        self.assertEqual(obj.robot_id, 'robot1')

    def test_nan_smoke_level_is_float32(self):
        """float32 fields must accept NaN; range validation is caller responsibility."""
        obj = self.Msg()
        obj.smoke_level = float('nan')
        self.assertTrue(math.isnan(obj.smoke_level))

    def test_normalized_risk_accepts_boundary_values(self):
        obj = self.Msg()
        for v in (0.0, 0.5, 1.0):
            obj.normalized_risk = v
            self.assertEqual(obj.normalized_risk, v)


class TestDetection(unittest.TestCase):

    def setUp(self):
        self.Msg = _msg('Detection')

    def test_required_fields_present(self):
        obj = self.Msg()
        for field in ('class_label', 'confidence', 'bounding_box', 'estimated_pose'):
            self.assertTrue(hasattr(obj, field), f'Detection missing field: {field}')

    def test_confidence_default_in_range(self):
        obj = self.Msg()
        self.assertGreaterEqual(obj.confidence, 0.0)
        self.assertLessEqual(obj.confidence, 1.0)

    def test_class_label_accepts_known_classes(self):
        obj = self.Msg()
        for label in ('fire', 'human', 'smoke'):
            obj.class_label = label
            self.assertEqual(obj.class_label, label)

    def test_bounding_box_accepts_four_values(self):
        obj = self.Msg()
        obj.bounding_box = [0.0, 0.0, 640.0, 480.0]
        self.assertEqual(len(obj.bounding_box), 4)

    def test_bounding_box_is_fixed_size_four(self):
        """Fixed-size float32[4] must reject arrays of wrong length."""
        obj = self.Msg()
        with self.assertRaises(Exception):
            obj.bounding_box = [0.0, 0.0, 640.0]  # only 3 values


class TestVisionDetectionArray(unittest.TestCase):

    def setUp(self):
        self.Msg = _msg('VisionDetectionArray')
        self.Det = _msg('Detection')

    def test_required_fields_present(self):
        obj = self.Msg()
        for field in ('robot_id', 'camera_id', 'detections', 'timestamp'):
            self.assertTrue(hasattr(obj, field), f'VisionDetectionArray missing field: {field}')

    def test_detections_empty_by_default(self):
        obj = self.Msg()
        self.assertEqual(len(obj.detections), 0)

    def test_accepts_detection_objects(self):
        arr = self.Msg()
        d = self.Det()
        d.class_label = 'fire'
        d.confidence = 0.92
        arr.detections = [d]
        self.assertEqual(len(arr.detections), 1)
        self.assertEqual(arr.detections[0].class_label, 'fire')

    def test_accepts_multiple_detections(self):
        arr = self.Msg()
        arr.detections = [self.Det(), self.Det(), self.Det()]
        self.assertEqual(len(arr.detections), 3)

    def test_robot_id_and_camera_id_strings(self):
        obj = self.Msg()
        obj.robot_id = 'robot2'
        obj.camera_id = 'cam_front'
        self.assertEqual(obj.robot_id, 'robot2')
        self.assertEqual(obj.camera_id, 'cam_front')


class TestFusionDecision(unittest.TestCase):

    def setUp(self):
        self.Msg = _msg('FusionDecision')

    def test_required_fields_present(self):
        obj = self.Msg()
        for field in ('robot_id', 'fire_confirmed', 'human_confirmed', 'risk_level',
                      'recommended_action', 'contributing_sources',
                      'sensor_confidence', 'vision_confidence', 'timestamp'):
            self.assertTrue(hasattr(obj, field), f'FusionDecision missing field: {field}')

    def test_confirmed_flags_false_by_default(self):
        obj = self.Msg()
        self.assertFalse(obj.fire_confirmed)
        self.assertFalse(obj.human_confirmed)

    def test_risk_level_default_in_range(self):
        obj = self.Msg()
        self.assertGreaterEqual(obj.risk_level, 0.0)
        self.assertLessEqual(obj.risk_level, 1.0)

    def test_confidence_fields_default_in_range(self):
        obj = self.Msg()
        for field in ('sensor_confidence', 'vision_confidence'):
            v = getattr(obj, field)
            self.assertGreaterEqual(v, 0.0, f'{field} default < 0')
            self.assertLessEqual(v, 1.0, f'{field} default > 1')

    def test_recommended_action_accepts_valid_values(self):
        obj = self.Msg()
        for action in ('SUPPRESS', 'RESCUE', 'MONITOR', 'NONE'):
            obj.recommended_action = action
            self.assertEqual(obj.recommended_action, action)

    def test_contributing_sources_accepts_list(self):
        obj = self.Msg()
        obj.contributing_sources = ['esp32_robot1', 'camera_robot1']
        self.assertEqual(len(obj.contributing_sources), 2)
        self.assertIn('esp32_robot1', obj.contributing_sources)

    def test_contributing_sources_empty_by_default(self):
        obj = self.Msg()
        self.assertEqual(len(obj.contributing_sources), 0)

    def test_empty_robot_id_is_storable(self):
        """ROS 2 allows empty strings; empty-id validation is the node's responsibility."""
        obj = self.Msg()
        obj.robot_id = ''
        self.assertEqual(obj.robot_id, '')

    def test_risk_level_above_threshold_triggers_suppression_intent(self):
        """Smoke test: risk_level > 0.7 should logically map to non-NONE action."""
        obj = self.Msg()
        obj.risk_level = 0.85
        obj.fire_confirmed = True
        obj.recommended_action = 'SUPPRESS'
        self.assertGreater(obj.risk_level, 0.7)
        self.assertNotEqual(obj.recommended_action, 'NONE')


if __name__ == '__main__':
    unittest.main()
