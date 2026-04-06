"""Metrics exporter helper."""

import json


def export_metrics(metrics):
    return json.dumps(metrics, sort_keys=True)


def main():
    print('metrics_exporter_node v1 ready')


if __name__ == '__main__':
    main()
