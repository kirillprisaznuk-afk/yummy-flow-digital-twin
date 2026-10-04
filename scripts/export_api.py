"""Export the actual API contract without connecting to a database."""

import json
from pathlib import Path

from app.main import create_app

target = Path(__file__).resolve().parents[1] / "frontend/api/openapi.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
