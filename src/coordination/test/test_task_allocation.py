from coordination.task_allocator import assign_task


def test_task_allocation_selects_lowest_bid():
    assignment = assign_task('task-1', {'robot1': 5.0, 'robot2': 3.5, 'robot3': 4.2})
    assert assignment['winner'] == 'robot2'
    assert assignment['bid_count'] == 3


def test_task_allocation_tie_breaks_by_robot_id():
    assignment = assign_task('task-2', {'robot2': 1.0, 'robot1': 1.0})
    assert assignment['winner'] == 'robot1'

