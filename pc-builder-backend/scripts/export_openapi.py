import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

(ROOT / "openapi.json").write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print("openapi.json updated")
