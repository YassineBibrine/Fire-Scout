"""Fault reassignment helpers for degraded mission mode."""

from coordination.task_allocator import choose_winner


def reassign_tasks(assignments, failed_robot_id, replacement_bids):
    """Reassign tasks owned by a failed robot using replacement bids.

    Args:
        assignments: dict mapping task_id -> robot_id
        failed_robot_id: robot id considered faulty
        replacement_bids: dict task_id -> dict robot_id -> cost
    """
    result = dict(assignments)
    for task_id, owner in assignments.items():
        if owner != failed_robot_id:
            continue

        winner = choose_winner(replacement_bids.get(task_id, {}))
        result[task_id] = winner
    return result
