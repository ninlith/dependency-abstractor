import sys
from pathlib import Path
sys.path.insert(1, str(Path(__file__).resolve().parent))
from script import __version__, main
