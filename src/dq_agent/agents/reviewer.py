from __future__ import annotations

import re
from typing import List

from dq_agent.models import ReviewIssue, TableMeta


class SqlReviewAgent:
    """Basic SQL review for generated HiveSQL.

    This is not a full SQL parser. It catches high-value risks that commonly hurt Hive clusters.
    """

    def review(self, sql: str, table: TableMeta | None = None) -> List[ReviewIssue]:
        issues: List[ReviewIssue] = []
        normalized = self._normalize(sql)

        if "select *" in normalized:
            issues.append(
                ReviewIssue(
                    level="WARN",
                    code="SELECT_STAR",
                    message="SQL 中出现 SELECT *，大表巡检建议只选择必要字段。",
                )
            )

        if table:
            table_name = table.table_name.lower()
            partition_col = table.partition_column.lower()
            table_hit = table_name in normalized
            partition_hit = re.search(rf"where\s+`?{re.escape(partition_col)}`?\s*=", normalized) is not None
            if table_hit and not partition_hit:
                issues.append(
                    ReviewIssue(
                        level="ERROR",
                        code="NO_PARTITION_FILTER",
                        message=f"检测到表 {table.table_name}，但未发现分区过滤 {table.partition_column}=...，存在全表扫描风险。",
                    )
                )

        union_count = len(re.findall(r"\bunion\s+all\b", normalized))
        if union_count > 80:
            issues.append(
                ReviewIssue(
                    level="WARN",
                    code="TOO_MANY_UNION_ALL",
                    message=f"SQL 中 UNION ALL 数量为 {union_count}，规则过多时建议拆分为多个巡检任务。",
                )
            )

        if "insert overwrite table" in normalized:
            issues.append(
                ReviewIssue(
                    level="INFO",
                    code="OVERWRITE_PARTITION",
                    message="当前使用 INSERT OVERWRITE 写入结果分区，重复执行同一天任务会覆盖历史结果。",
                )
            )

        if not issues:
            issues.append(
                ReviewIssue(
                    level="INFO",
                    code="PASS",
                    message="未发现明显风险。",
                )
            )

        return issues

    @staticmethod
    def _normalize(sql: str) -> str:
        sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        sql = re.sub(r"\s+", " ", sql)
        return sql.strip().lower()
