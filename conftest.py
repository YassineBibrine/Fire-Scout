"""Workspace-wide pytest configuration.

Ensures each ROS Python package under src/ is importable when tests are run
individually from the workspace root (without manual PYTHONPATH setup).
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'

for package_dir in SRC.iterdir():
    if not package_dir.is_dir():
        continue
    if (package_dir / 'setup.py').exists() and str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))
