#!/usr/bin/env python3
import unittest
from importlib import import_module

class TestMessageGeneration(unittest.TestCase):
    
    def test_all_messages_exist(self):
        """Test that all expected messages can be imported"""
        messages = [
            'RobotHealth', 'Frontier', 'FrontierArray', 
            'FireDetection', 'HumanDetection', 'TaskAssignment',
            'NodeStatus', 'Incident', 'FaultEvent', 'MissionState',
            'MapMergeStatus', 'ReferenceTrajectory', 'SensorData',
            'AuctionAnnouncement', 'AuctionBid', 'AuctionResult'
        ]
        
        for msg in messages:
            with self.subTest(msg=msg):
                try:
                    module = import_module('firescout_interfaces.msg')
                    getattr(module, msg)
                except (ImportError, AttributeError) as e:
                    self.fail(f"Message {msg} not found: {e}")
    
    def test_robot_health_fields(self):
        """Test RobotHealth message has required fields"""
        from firescout_interfaces.msg import RobotHealth
        
        msg = RobotHealth()
        self.assertTrue(hasattr(msg, 'robot_name'))
        self.assertTrue(hasattr(msg, 'battery_percentage'))
        self.assertTrue(hasattr(msg, 'cpu_load'))
        self.assertTrue(hasattr(msg, 'memory_usage'))
        self.assertTrue(hasattr(msg, 'temperature'))
        self.assertTrue(hasattr(msg, 'is_connected'))
        self.assertTrue(hasattr(msg, 'timestamp'))
    
    def test_frontier_fields(self):
        """Test Frontier message has required fields"""
        from firescout_interfaces.msg import Frontier
        
        msg = Frontier()
        self.assertTrue(hasattr(msg, 'centroid'))
        self.assertTrue(hasattr(msg, 'size'))
        self.assertTrue(hasattr(msg, 'cost'))
        self.assertTrue(hasattr(msg, 'gain'))

if __name__ == '__main__':
    unittest.main()
