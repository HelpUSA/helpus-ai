import sys
import os
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    os.chdir(str(backend_dir))
except Exception:
    pass

from main import app as app
