from common_utils.namespace_utils import namespaced


def test_namespaced_topic():
    assert namespaced('robot1', '/scan') == '/robot1/scan'
