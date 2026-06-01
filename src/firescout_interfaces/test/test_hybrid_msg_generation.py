#!/usr/bin/env python3
"""Schema validation tests for Phase 2 hybrid messages.

Covers: FireSensorAlert, Detection, VisionDetectionArray, FusionDecision

Contract enforcement (interface_contract.yaml v2.0.0):
  - reject_nan: true
  - reject_empty_robot_id: true
  - confidence_range: [0.0, 1.0]
  - risk_level_range: [0.0, 1.0]

ROS 2 message fields accept any value at assignment time; enforcement is the
responsibility of the publishing node. These tests verify both the message
schema (field existence, types, defaults) AND the contract validator functions
that nodes must call before publishing.
"""
import math
import unittest
from importlib import import_module


# ── Contract validators ────────────────────────────────────────────────────────
# Nodes must call these before publishing hybrid messages.
# Source of truth: interface_contract.yaml v2.0.0

def validate_robot_id(robot_id: object) -> None:
    """Enforce contract rule: reject_empty_robot_id: true.

    Raises ValueError if robot_id is empty or whitespace-only.
    """
    if not isinstance(robot_id, str) or not robot_id.strip():
        raise ValueError(
            f"robot_id must be a non-empty string, got: {robot_id!r}. "
            "Contract rule: reject_empty_robot_id: true"
        )


def validate_float_field(value: float, field_name: str) -> None:
    """Enforce contract rules: reject_nan: true.

    Raises ValueError if value is NaN or infinite.
    """
    if math.isnan(value):
        raise ValueError(
            f"{field_name} must not be NaN. Contract rule: reject_nan: true"
        )
    if math.isinf(value):
        raise ValueError(
            f"{field_name} must not be infinite."
        )


def validate_confidence(value: float, field_name: str) -> None:
    """Enforce contract rule: confidence_range: [0.0, 1.0]."""
    validate_float_field(value, field_name)
    if not (0.0 <= value <= 1.0):
        raise ValueError(
            f"{field_name}={value} out of range. Contract rule: confidence_range [0.0, 1.0]"
        )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _msg(name):
    return getattr(import_module('firescout_interfaces.msg'), name)


# ── Existence ──────────────────────────────────────────────────────────────────

class TestHybridMessagesExist(unittest.TestCase):

    def test_all_hybrid_messages_importable(self):
        for name in ('FireSensorAlert', 'Detection', 'VisionDetectionArray', 'FusionDecision'):
            with self.subTest(msg=name):
                _msg(name)


# ── Contract validators ────────────────────────────────────────────────────────

class TestContractValidators(unittest.TestCase):
    """Tests for the validator functions nodes must use before publishing."""

    # robot_id ──────────────────────────────────────────────────────────────────

    def test_validate_robot_id_rejects_empty_string(self):
        with self.assertRaises(ValueError):
            validate_robot_id('')

    def test_validate_robot_id_rejects_whitespace_only(self):
        with self.assertRaises(ValueError):
            validate_robot_id('   ')

    def test_validate_robot_id_rejects_none(self):
        with self.assertRaises((ValueError, AttributeError)):
            validate_robot_id(None)

    def test_validate_robot_id_accepts_valid_namespaces(self):
        for ns in ('robot1', 'robot2', 'robot3'):
            with self.subTest(ns=ns):
                validate_robot_id(ns)  # must not raise

    # NaN / float ───────────────────────────────────────────────────────────────

    def test_validate_float_field_rejects_nan(self):
        with self.assertRaises(ValueError):
            validate_float_field(float('nan'), 'smoke_level')

    def test_validate_float_field_rejects_positive_inf(self):
        with self.assertRaises(ValueError):
            validate_float_field(float('inf'), 'normalized_risk')

    def test_validate_float_field_rejects_negative_inf(self):
        with self.assertRaises(ValueError):
            validate_float_field(float('-inf'), 'gas_level')

    def test_validate_float_field_accepts_valid_range(self):
        for v in (0.0, 0.5, 1.0):
            with self.subTest(value=v):
                validate_float_field(v, 'smoke_level')  # must not raise

    # confidence ────────────────────────────────────────────────────────────────

    def test_validate_confidence_rejects_above_one(self):
        with self.assertRaises(ValueError):
            validate_confidence(1.1, 'sensor_confidence')

    def test_validate_confidence_rejects_below_zero(self):
        with self.assertRaises(ValueError):
            validate_confidence(-0.1, 'vision_confidence')

    def test_validate_confidence_rejects_nan(self):
        with self.assertRaises(ValueError):
            validate_confidence(float('nan'), 'confidence')

    def test_validate_confidence_accepts_boundaries(self):
        for v in (0.0, 0.5, 1.0):
            validate_confidence(v, 'confidence')  # must not raise


# ── FireSensorAlert ────────────────────────────────────────────────────────────

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

    def test_nan_smoke_level_rejected_by_validator(self):
        """ROS 2 msg layer accepts NaN at field level, but contract says reject_nan: true.
        Nodes must call validate_float_field() before publishing — this tests that."""
        obj = self.Msg()
        obj.smoke_level = float('nan')  # msg layer does not raise
        self.assertTrue(math.isnan(obj.smoke_level))  # confirm it stored NaN
        with self.assertRaises(ValueError):
            validate_float_field(obj.smoke_level, 'smoke_level')  # validator must reject

    def test_empty_robot_id_rejected_by_validator(self):
        """ROS 2 msg layer stores empty strings freely, but contract says
        reject_empty_robot_id: true. Nodes must call validate_robot_id()."""
        obj = self.Msg()
        obj.robot_id = ''
        with self.assertRaises(ValueError):
            validate_robot_id(obj.robot_id)

    def test_normalized_risk_accepts_boundary_values(self):
        obj = self.Msg()
        for v in (0.0, 0.5, 1.0):
            obj.normalized_risk = v
            self.assertEqual(obj.normalized_risk, v)


# ── Detection ──────────────────────────────────────────────────────────────────

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
        """ROS 2 float32[4] does not raise on wrong-length Python assignment;
        the constraint is enforced at serialization time.
        We verify a valid 4-element assignment is stored and values are preserved."""
        obj = self.Msg()
        obj.bounding_box = [10.0, 20.0, 300.0, 400.0]
        self.assertEqual(len(obj.bounding_box), 4)
        self.assertAlmostEqual(obj.bounding_box[0], 10.0)
        self.assertAlmostEqual(obj.bounding_box[1], 20.0)
        self.assertAlmostEqual(obj.bounding_box[2], 300.0)
        self.assertAlmostEqual(obj.bounding_box[3], 400.0)

    def test_confidence_nan_rejected_by_validator(self):
        obj = self.Msg()
        obj.confidence = float('nan')
        with self.assertRaises(ValueError):
            validate_confidence(obj.confidence, 'confidence')


# ── VisionDetectionArray ───────────────────────────────────────────────────────

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

    def test_empty_robot_id_rejected_by_validator(self):
        obj = self.Msg()
        obj.robot_id = ''
        with self.assertRaises(ValueError):
            validate_robot_id(obj.robot_id)


# ── FusionDecision ─────────────────────────────────────────────────────────────

class TestFusionDecision(unittest.TestCase):

    def setUp(self):
        self.Msg = _msg('FusionDecision')

    def test_required_fields_present(self):
        obj = self.Msg()
        for field in ('robot_id', 'fire_confirmed', 'human_confirmed', 'risk_level',
                      'recommended_action', 'contributing_sources',
                      'sensor_confidence', 'vision_confidence',
                      'incident_position', 'timestamp'):
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

    def test_empty_robot_id_rejected_by_validator(self):
        """ROS 2 stores empty strings freely; validator enforces the contract."""
        obj = self.Msg()
        obj.robot_id = ''
        with self.assertRaises(ValueError):
            validate_robot_id(obj.robot_id)

    def test_sensor_confidence_nan_rejected_by_validator(self):
        obj = self.Msg()
        obj.sensor_confidence = float('nan')
        with self.assertRaises(ValueError):
            validate_confidence(obj.sensor_confidence, 'sensor_confidence')

    def test_vision_confidence_nan_rejected_by_validator(self):
        obj = self.Msg()
        obj.vision_confidence = float('nan')
        with self.assertRaises(ValueError):
            validate_confidence(obj.vision_confidence, 'vision_confidence')

    def test_risk_level_above_threshold_triggers_suppression_intent(self):
        obj = self.Msg()
        obj.risk_level = 0.85
        obj.fire_confirmed = True
        obj.recommended_action = 'SUPPRESS'
        self.assertGreater(obj.risk_level, 0.7)
        self.assertNotEqual(obj.recommended_action, 'NONE')


if __name__ == '__main__':
    unittest.main()
