#!/usr/bin/env python3
import unittest
from importlib import import_module

class TestServiceGeneration(unittest.TestCase):
    
    def test_all_services_exist(self):
        """Test that all expected services can be imported"""
        services = [
            'AssignTask', 'StartMapping', 'StopMapping', 
            'SetRobotMode', 'AckTask', 'GetRobotState',
            'ReportFault', 'RequestAssistance', 'ResolveIncident',
            'SetMapMergeEnabled'
        ]
        
        for srv in services:
            with self.subTest(srv=srv):
                try:
                    module = import_module('firescout_interfaces.srv')
                    getattr(module, srv)
                except (ImportError, AttributeError) as e:
                    self.fail(f"Service {srv} not found: {e}")
    
    def test_assign_task_fields(self):
        """Test AssignTask service has required fields"""
        module = import_module('firescout_interfaces.srv')
        AssignTask = getattr(module, 'AssignTask')
        
        # Check Request fields
        self.assertTrue(hasattr(AssignTask.Request, 'task_id'))
        self.assertTrue(hasattr(AssignTask.Request, 'task_type'))
        self.assertTrue(hasattr(AssignTask.Request, 'target_robot'))
        self.assertTrue(hasattr(AssignTask.Request, 'target_pose'))
        self.assertTrue(hasattr(AssignTask.Request, 'priority'))
        
        # Check Response fields
        self.assertTrue(hasattr(AssignTask.Response, 'success'))
        self.assertTrue(hasattr(AssignTask.Response, 'message'))

if __name__ == '__main__':
    unittest.main()
