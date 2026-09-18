"""Validate and check public external course links before a release."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
os.chdir(API_ROOT)
sys.path.insert(0, str(API_ROOT))

from app.database import SessionLocal  # noqa: E402
from app.services.resources import list_resources  # noqa: E402
from app.services.resource_health import check_resource_links  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="巡检已维护的外部课程资源链接。")
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "output" / "external-resource-health.json",
        help="JSON 报告输出位置。默认写入 output/external-resource-health.json。",
    )
    parser.add_argument("--timeout", type=float, default=15, help="单个外链超时秒数。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with SessionLocal() as session:
        results = check_resource_links(list_resources(session), timeout_seconds=args.timeout)

    report = [result.to_dict() for result in results]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in results:
        code = str(result.status_code) if result.status_code else "-"
        print(f"[{result.outcome:9}] {code:>3} {result.id}: {result.detail}")
    failures = [result for result in results if result.outcome in {"invalid", "failed"}]
    print(f"报告：{args.report}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
