#!/usr/bin/env python3
import unittest
from importlib import import_module

class TestActionGeneration(unittest.TestCase):
    
    def test_all_actions_exist(self):
        """Test that all expected actions can be imported"""
        actions = ['SuppressFire', 'RescueHuman']
        
        for action in actions:
            with self.subTest(action=action):
                try:
                    module = import_module('firescout_interfaces.action')
                    getattr(module, action)
                except (ImportError, AttributeError) as e:
                    self.fail(f"Action {action} not found: {e}")
    
    def test_suppress_fire_fields(self):
        """Test SuppressFire action has required fields"""
        module = import_module('firescout_interfaces.action')
        SuppressFire = getattr(module, 'SuppressFire')
        
        # Check Goal fields
        self.assertTrue(hasattr(SuppressFire.Goal, 'fire_id'))
        self.assertTrue(hasattr(SuppressFire.Goal, 'fire_location'))
        self.assertTrue(hasattr(SuppressFire.Goal, 'required_water_volume'))
        self.assertTrue(hasattr(SuppressFire.Goal, 'estimated_duration'))
        
        # Check Result fields
        self.assertTrue(hasattr(SuppressFire.Result, 'success'))
        self.assertTrue(hasattr(SuppressFire.Result, 'message'))
        self.assertTrue(hasattr(SuppressFire.Result, 'water_used'))
        self.assertTrue(hasattr(SuppressFire.Result, 'suppression_time_seconds'))
        
        # Check Feedback fields
        self.assertTrue(hasattr(SuppressFire.Feedback, 'progress'))
        self.assertTrue(hasattr(SuppressFire.Feedback, 'remaining_water'))

if __name__ == '__main__':
    unittest.main()
