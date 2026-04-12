import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

MONTHS = list(range(13))
THRESHOLD_MM = float(os.getenv("PIPE_WALL_THRESHOLD_MM", "5.0"))
