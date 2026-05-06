from pathlib import Path


def test_rviz_fixed_frame_is_under_global_options():
    rviz_path = Path(__file__).resolve().parents[1] / 'config' / 'firescout_viz.rviz'

    in_visualization_manager = False
    in_global_options = False
    fixed_frame = None
    misplaced_fixed_frame = None

    for line in rviz_path.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip(' '))

        if indent == 0:
            in_visualization_manager = stripped == 'Visualization Manager:'
            in_global_options = False
            continue

        if not in_visualization_manager:
            continue

        if indent == 2:
            if stripped.startswith('Fixed Frame:'):
                misplaced_fixed_frame = stripped.split(':', 1)[1].strip()
            in_global_options = stripped == 'Global Options:'
            continue

        if in_global_options and indent == 4 and stripped.startswith('Fixed Frame:'):
            fixed_frame = stripped.split(':', 1)[1].strip()

    assert fixed_frame == 'map'
    assert misplaced_fixed_frame is None
