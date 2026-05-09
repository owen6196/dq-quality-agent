from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List


class ReportAgent:
    """Create a human-readable summary from exported DQ result CSV.

    Expected CSV columns:
    rule_id, table_name, rule_type, field_name, field_value, biz_key, error_reason, severity, check_time, dt
    """

    def summarize_csv(self, csv_path: str | Path, top_n: int = 10) -> str:
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"result csv not found: {path}")

        rows: List[Dict[str, str]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        if not rows:
            return "本次数据质量巡检未发现异常。"

        severity_counter = Counter(row.get("severity", "UNKNOWN") for row in rows)
        rule_counter = Counter(row.get("rule_type", "UNKNOWN") for row in rows)
        field_counter = Counter(row.get("field_name", "UNKNOWN") for row in rows)

        lines = [
            "# 数据质量巡检摘要",
            "",
            f"异常总数：{len(rows)}",
            "",
            "## 按严重等级",
            *self._counter_lines(severity_counter),
            "",
            "## 按规则类型",
            *self._counter_lines(rule_counter),
            "",
            "## Top 异常字段",
            *self._counter_lines(field_counter, top_n=top_n),
            "",
            "## 处理建议",
        ]

        if severity_counter.get("CRITICAL", 0) > 0:
            lines.append("- 存在 CRITICAL 异常，建议阻断下游任务或暂停数据发布。")
        if rule_counter.get("PARTITION_NOT_EMPTY", 0) > 0:
            lines.append("- 分区无数据，优先检查上游调度依赖、数据同步链路和分区参数。")
        if rule_counter.get("UNIQUE_KEY", 0) > 0:
            lines.append("- 主键重复，优先检查明细表去重逻辑、增量合并逻辑和源系统重复推送。")
        if rule_counter.get("ENUM_CODE", 0) > 0:
            lines.append("- 码表值域异常，确认标准码表是否需要新增编码，或上游是否出现脏值。")
        if rule_counter.get("NOT_NULL", 0) > 0:
            lines.append("- 关键字段为空，检查上游字段映射和 JOIN 是否导致字段丢失。")

        return "\n".join(lines)

    @staticmethod
    def _counter_lines(counter: Counter, top_n: int = 20) -> List[str]:
        return [f"- {key}: {value}" for key, value in counter.most_common(top_n)]
