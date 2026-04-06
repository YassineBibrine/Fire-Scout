"""Namespace lint helpers for topic naming checks."""


def find_namespace_violations(namespaces, topics):
    allowed_prefixes = [f'/{ns}/' for ns in namespaces]
    violations = []
    for topic in topics:
        if topic == '/clock':
            continue
        if any(topic.startswith(prefix) for prefix in allowed_prefixes):
            continue
        violations.append(topic)
    return violations


def main():
    print('namespace_lint_node v1 ready')


if __name__ == '__main__':
    main()
