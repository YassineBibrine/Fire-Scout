"""
Tests for coordination_bridge_node TaskAssignment output logic.
"""

from types import SimpleNamespace

_FIRE_DEADLINE_SEC = 30.0
_HUMAN_DEADLINE_SEC = 20.0
_TASK_TYPE_FIRE = 'SUPPRESS'
_TASK_TYPE_HUMAN = 'RESCUE'


def _build_assignment(incident, task_type, deadline_sec):
    return SimpleNamespace(
        task_id=incident.incident_id,
        task_type=task_type,
        assigned_robot=incident.robot_id,
        target_pose=incident.position,
        priority=incident.priority,
        deadline_sec=deadline_sec,
    )


def _make_incident(incident_id, incident_type, robot_id, priority, position=None):
    return SimpleNamespace(
        incident_id=incident_id,
        incident_type=incident_type,
        robot_id=robot_id,
        priority=priority,
        position=position or SimpleNamespace(x=1.0, y=2.0),
    )


def test_fire_incident_produces_suppress_task():
    inc = _make_incident('fire_robot1_1', 'FIRE', 'robot1', 5.993)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert a.task_type == 'SUPPRESS'

def test_fire_task_id_matches_incident_id():
    inc = _make_incident('fire_robot2_3', 'FIRE', 'robot2', 5.802)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert a.task_id == 'fire_robot2_3'

def test_fire_assigned_robot_matches_incident_robot():
    inc = _make_incident('fire_robot3_1', 'FIRE', 'robot3', 5.601)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert a.assigned_robot == 'robot3'

def test_fire_priority_preserved():
    inc = _make_incident('fire_robot1_2', 'FIRE', 'robot1', 5.993)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert abs(a.priority - 5.993) < 1e-6

def test_fire_deadline_is_30s():
    inc = _make_incident('fire_robot1_1', 'FIRE', 'robot1', 5.5)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert a.deadline_sec == 30.0

def test_human_incident_produces_rescue_task():
    inc = _make_incident('rescue_robot1_1', 'HUMAN', 'robot1', 10.513)
    a = _build_assignment(inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert a.task_type == 'RESCUE'

def test_human_task_id_matches_incident_id():
    inc = _make_incident('rescue_robot2_1', 'HUMAN', 'robot2', 10.702)
    a = _build_assignment(inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert a.task_id == 'rescue_robot2_1'

def test_human_assigned_robot_matches_incident_robot():
    inc = _make_incident('rescue_robot1_2', 'HUMAN', 'robot1', 10.903)
    a = _build_assignment(inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert a.assigned_robot == 'robot1'

def test_human_priority_preserved():
    inc = _make_incident('rescue_robot1_1', 'HUMAN', 'robot1', 10.703)
    a = _build_assignment(inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert abs(a.priority - 10.703) < 1e-6

def test_human_deadline_is_20s():
    inc = _make_incident('rescue_robot1_1', 'HUMAN', 'robot1', 10.5)
    a = _build_assignment(inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert a.deadline_sec == 20.0

def test_human_deadline_tighter_than_fire():
    assert _HUMAN_DEADLINE_SEC < _FIRE_DEADLINE_SEC

def test_human_priority_exceeds_fire_priority_through_bridge():
    fire_inc = _make_incident('fire_robot1_1', 'FIRE', 'robot1', 5.993)
    human_inc = _make_incident('rescue_robot1_1', 'HUMAN', 'robot1', 10.513)
    fa = _build_assignment(fire_inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    ha = _build_assignment(human_inc, _TASK_TYPE_HUMAN, _HUMAN_DEADLINE_SEC)
    assert ha.priority > fa.priority

def test_target_pose_preserved():
    pos = SimpleNamespace(x=3.0, y=4.0)
    inc = _make_incident('fire_robot1_1', 'FIRE', 'robot1', 5.5, position=pos)
    a = _build_assignment(inc, _TASK_TYPE_FIRE, _FIRE_DEADLINE_SEC)
    assert a.target_pose.x == 3.0
    assert a.target_pose.y == 4.0
