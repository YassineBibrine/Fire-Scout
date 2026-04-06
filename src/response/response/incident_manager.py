"""Incident queue helpers with priority ordering."""


def prioritize_incidents(incidents):
    """Sort incidents by descending priority, preserving deterministic order by type."""
    return sorted(incidents, key=lambda item: (-item['priority'], item['type']))
