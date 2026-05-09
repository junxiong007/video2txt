import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice_role.app import run

if __name__ == "__main__":
    run()
