"""Grid-based frontier extraction utilities."""


def extract_frontiers(grid):
    """Return frontier cells as (row, col) from occupancy grid.

    Convention: -1 unknown, 0 free, 100 occupied.
    A frontier is an unknown cell adjacent to at least one free cell.
    """
    if not grid or not grid[0]:
        return []

    rows = len(grid)
    cols = len(grid[0])
    out = []
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != -1:
                continue

            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    out.append((r, c))
                    break

    return out
