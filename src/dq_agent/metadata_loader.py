from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from dq_agent.models import ColumnMeta, ManualRule, TableMeta


class MetadataLoader:
    """Load table metadata from YAML.

    In real projects, this class can be replaced by Hive Metastore / DataHub / Atlas readers.
    """

    @staticmethod
    def load_yaml(path: str | Path) -> TableMeta:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"metadata file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f) or {}

        required = ["table_name", "partition_column", "columns"]
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"metadata missing required fields: {missing}")

        columns: List[ColumnMeta] = []
        for item in data.get("columns", []):
            columns.append(
                ColumnMeta(
                    name=str(item["name"]),
                    type=str(item.get("type", "string")),
                    comment=str(item.get("comment", "")),
                    nullable=bool(item.get("nullable", True)),
                    standard_encode=item.get("standard_encode"),
                )
            )

        manual_rules: List[ManualRule] = []
        for item in data.get("manual_rules", []) or []:
            manual_rules.append(
                ManualRule(
                    rule_type=str(item.get("rule_type", "CUSTOM_SQL")),
                    rule_id=str(item["rule_id"]),
                    field_name=str(item.get("field_name", "*")),
                    expression=str(item["expression"]),
                    reason=str(item.get("reason", item["rule_id"])),
                    severity=str(item.get("severity", "MEDIUM")),
                )
            )

        return TableMeta(
            database=str(data.get("database", "")),
            table_name=str(data["table_name"]),
            partition_column=str(data["partition_column"]),
            partition_value=str(data.get("partition_value", "${biz_date}")),
            primary_keys=[str(x) for x in data.get("primary_keys", [])],
            columns=columns,
            manual_rules=manual_rules,
        )
