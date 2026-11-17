"""JSON report serialization."""

import json
from typing import Any


def render_report(report: dict[str, Any], invalid_records: list[dict[str, Any]]) -> str:
    report["invalid_records"] = sorted(
        invalid_records,
        key=lambda item: (item.get("key", ""), item["row"], item["file"]),
    )
    return json.dumps(report, sort_keys=True, indent=2) + "\n"
