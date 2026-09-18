import json
from pathlib import Path

from app.main import app


def test_versioned_openapi_contract_matches_service() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    snapshot = json.loads((repository_root / "packages" / "contracts" / "openapi.json").read_text(encoding="utf-8"))
    assert snapshot == app.openapi()
