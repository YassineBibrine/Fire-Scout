from pathlib import Path


def test_namespace_isolation_contract_lists_unique_robots():
    cfg_file = Path(__file__).resolve().parents[1] / 'config' / 'namespace_map.yaml'
    text = cfg_file.read_text(encoding='utf-8')

    robots = [line.strip().lstrip('-').strip() for line in text.splitlines() if line.strip().startswith('-')]
    assert robots == ['robot1', 'robot2', 'robot3']
    assert len(set(robots)) == 3

