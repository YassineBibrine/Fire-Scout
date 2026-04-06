from mapping.tf_consistency import is_tf_consistent


def test_tf_consistency_detects_valid_tree():
    edges = [('map', 'odom'), ('odom', 'base_link'), ('base_link', 'laser')]
    assert is_tf_consistent(edges)


def test_tf_consistency_detects_cycle():
    edges = [('map', 'odom'), ('odom', 'base_link'), ('base_link', 'odom')]
    assert not is_tf_consistent(edges)

