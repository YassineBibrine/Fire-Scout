"""Simple TF graph checks for cycles and root reachability."""


def is_tf_consistent(edges, root='map'):
    """Validate a tree-like TF graph represented as parent->child edge tuples."""
    children = {}
    nodes = {root}
    for parent, child in edges:
        nodes.add(parent)
        nodes.add(child)
        children.setdefault(parent, []).append(child)

    visiting = set()
    visited = set()

    def dfs(node):
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        for child in children.get(node, []):
            if not dfs(child):
                return False
        visiting.remove(node)
        visited.add(node)
        return True

    if not dfs(root):
        return False

    return nodes.issubset(visited)
