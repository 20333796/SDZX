import json
import sys
from pathlib import Path

repository_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repository_root / "apps" / "api"))

from app.main import app  # noqa: E402

output_path = repository_root / "packages" / "contracts" / "openapi.json"
output_path.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(output_path)
