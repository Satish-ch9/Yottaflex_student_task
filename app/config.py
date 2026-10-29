from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SAMPLE_DIR = DATA_DIR / "sample"
EXPORT_DIR = DATA_DIR / "exports"
DEFAULT_SEED = 20261022
TERM_ID = "TERM-2026-FALL"

for folder in (DATA_DIR, SAMPLE_DIR, EXPORT_DIR):
    folder.mkdir(parents=True, exist_ok=True)
