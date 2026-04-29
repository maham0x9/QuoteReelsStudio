import os
import sys
from pathlib import Path

# Make repo importable when pytest is run from anywhere.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Run all Qt code in a head-less mode.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
