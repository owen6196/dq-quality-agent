from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleType(str, Enum):
    NOT_NULL = "NOT_NULL"
    ENUM_CODE = "ENUM_CODE"
    UNIQUE_KEY = "UNIQUE_KEY"
    NON_NEGATIVE = "NON_NEGATIVE"
    FUTURE_DATE = "FUTURE_DATE"
    PARTITION_NOT_EMPTY = "PARTITION_NOT_EMPTY"
    CUSTOM_SQL = "CUSTOM_SQL"


@dataclass
class ColumnMeta:
    name: str
    type: str
    comment: str = ""
    nullable: bool = True
    standard_encode: Optional[str] = None

    @property
    def lower_name(self) -> str:
        return self.name.lower()

    @property
    def lower_type(self) -> str:
        return self.type.lower()

    def is_number(self) -> bool:
        number_types = ["int", "bigint", "double", "float", "decimal", "numeric"]
        return any(t in self.lower_type for t in number_types)

    def is_date_like(self) -> bool:
        names = ["date", "time", "dt", "timestamp"]
        type_hit = any(t in self.lower_type for t in ["date", "time", "timestamp"])
        name_hit = any(self.lower_name.endswith(suffix) for suffix in names)
        return type_hit or name_hit

    def is_amount_like(self) -> bool:
        amount_keywords = [
            "amount", "amt", "fee", "price", "money", "cost", "charge", "total",
            "金额", "费用", "价格", "总额", "收费", "单价",
        ]
        text = f"{self.name} {self.comment}".lower()
        return self.is_number() and any(k.lower() in text for k in amount_keywords)


@dataclass
class ManualRule:
    rule_type: str
    rule_id: str
    field_name: str
    expression: str
    reason: str
    severity: str = Severity.MEDIUM.value


@dataclass
class TableMeta:
    database: str
    table_name: str
    partition_column: str
    partition_value: str = "${biz_date}"
    primary_keys: List[str] = field(default_factory=list)
    columns: List[ColumnMeta] = field(default_factory=list)
    manual_rules: List[ManualRule] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        if self.database:
            return f"{self.database}.{self.table_name}"
        return self.table_name

    def get_column(self, name: str) -> Optional[ColumnMeta]:
        target = name.lower()
        for col in self.columns:
            if col.name.lower() == target:
                return col
        return None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RulePlan:
    rule_id: str
    rule_type: str
    table_name: str
    field_name: str
    severity: str
    reason: str
    expression: Optional[str] = None
    standard_encode: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReviewIssue:
    level: str
    code: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
