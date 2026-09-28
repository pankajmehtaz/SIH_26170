"""
Backend ML bridge importing from root ml package.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import ml
    from ml import synthetic, features, models, evaluation
except ImportError:
    pass
