from __future__ import annotations

from typing import List

from dq_agent.models import RulePlan, RuleType, Severity, TableMeta


class PlannerAgent:
    """Plan data quality rules from table metadata.

    The class intentionally uses deterministic logic so the generated checks are stable.
    You can plug an LLM before/after this planner in real production, but the baseline should be reliable.
    """

    def build_plan(self, table: TableMeta) -> List[RulePlan]:
        plans: List[RulePlan] = []

        plans.append(
            RulePlan(
                rule_id=f"{table.table_name}__partition_not_empty",
                rule_type=RuleType.PARTITION_NOT_EMPTY.value,
                table_name=table.full_name,
                field_name=table.partition_column,
                severity=Severity.CRITICAL.value,
                reason=f"分区 {table.partition_column}={table.partition_value} 无数据",
            )
        )

        if table.primary_keys:
            plans.append(
                RulePlan(
                    rule_id=f"{table.table_name}__unique_key__{'_'.join(table.primary_keys)}",
                    rule_type=RuleType.UNIQUE_KEY.value,
                    table_name=table.full_name,
                    field_name=",".join(table.primary_keys),
                    severity=Severity.CRITICAL.value,
                    reason="主键组合重复",
                    extra={"keys": table.primary_keys},
                )
            )

        primary_key_set = {x.lower() for x in table.primary_keys}

        for col in table.columns:
            is_pk = col.name.lower() in primary_key_set
            if is_pk or col.nullable is False:
                plans.append(
                    RulePlan(
                        rule_id=f"{table.table_name}__not_null__{col.name}",
                        rule_type=RuleType.NOT_NULL.value,
                        table_name=table.full_name,
                        field_name=col.name,
                        severity=Severity.HIGH.value if not is_pk else Severity.CRITICAL.value,
                        reason=f"字段 {col.name} 为空",
                    )
                )

            if col.standard_encode:
                plans.append(
                    RulePlan(
                        rule_id=f"{table.table_name}__enum_code__{col.name}__{col.standard_encode}",
                        rule_type=RuleType.ENUM_CODE.value,
                        table_name=table.full_name,
                        field_name=col.name,
                        severity=Severity.HIGH.value,
                        reason=f"字段 {col.name} 不在标准码表 {col.standard_encode} 中",
                        standard_encode=col.standard_encode,
                    )
                )

            if col.is_amount_like():
                plans.append(
                    RulePlan(
                        rule_id=f"{table.table_name}__non_negative__{col.name}",
                        rule_type=RuleType.NON_NEGATIVE.value,
                        table_name=table.full_name,
                        field_name=col.name,
                        severity=Severity.MEDIUM.value,
                        reason=f"金额/费用字段 {col.name} 小于 0",
                    )
                )

            if col.is_date_like() and col.name.lower() != table.partition_column.lower():
                plans.append(
                    RulePlan(
                        rule_id=f"{table.table_name}__future_date__{col.name}",
                        rule_type=RuleType.FUTURE_DATE.value,
                        table_name=table.full_name,
                        field_name=col.name,
                        severity=Severity.MEDIUM.value,
                        reason=f"日期时间字段 {col.name} 晚于业务日期后一天",
                    )
                )

        for rule in table.manual_rules:
            plans.append(
                RulePlan(
                    rule_id=rule.rule_id,
                    rule_type=rule.rule_type,
                    table_name=table.full_name,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    reason=rule.reason,
                    expression=rule.expression,
                )
            )

        return self._deduplicate(plans)

    @staticmethod
    def _deduplicate(plans: List[RulePlan]) -> List[RulePlan]:
        seen = set()
        result = []
        for plan in plans:
            key = plan.rule_id
            if key in seen:
                continue
            seen.add(key)
            result.append(plan)
        return result
