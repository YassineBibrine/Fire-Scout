"""Map merge status helpers."""


def map_merge_status(available_maps, minimum_required=2):
    count = len(available_maps)
    return {
        'map_count': count,
        'ready': count >= minimum_required,
    }
