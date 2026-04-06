from coordination.fault_supervisor import reassign_tasks


def test_fault_reassignment_moves_tasks_from_failed_robot():
    assignments = {'t1': 'robot1', 't2': 'robot2', 't3': 'robot1'}
    replacement_bids = {
        't1': {'robot2': 2.0, 'robot3': 1.0},
        't3': {'robot2': 1.5},
    }

    updated = reassign_tasks(assignments, 'robot1', replacement_bids)
    assert updated['t1'] == 'robot3'
    assert updated['t3'] == 'robot2'
    assert updated['t2'] == 'robot2'

