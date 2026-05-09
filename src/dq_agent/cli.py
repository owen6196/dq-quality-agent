from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dq_agent.agents.planner import PlannerAgent
from dq_agent.agents.report_agent import ReportAgent
from dq_agent.agents.reviewer import SqlReviewAgent
from dq_agent.agents.sql_generator import HiveSqlGeneratorAgent
from dq_agent.metadata_loader import MetadataLoader


def cmd_plan(args: argparse.Namespace) -> int:
    table = MetadataLoader.load_yaml(args.metadata)
    plans = PlannerAgent().build_plan(table)
    data = [p.to_dict() for p in plans]
    output = json.dumps(data, ensure_ascii=False, indent=2)
    _write_or_print(output, args.output)
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    table = MetadataLoader.load_yaml(args.metadata)
    plans = PlannerAgent().build_plan(table)
    generator = HiveSqlGeneratorAgent(
        quality_table=args.quality_table,
        code_table=args.code_table,
    )
    sql = generator.generate(table=table, plans=plans, biz_date=args.biz_date)
    _write_or_print(sql, args.output)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    sql_path = Path(args.sql)
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")
    sql = sql_path.read_text(encoding="utf-8")

    table = MetadataLoader.load_yaml(args.metadata) if args.metadata else None
    issues = SqlReviewAgent().review(sql, table=table)
    output = json.dumps([i.to_dict() for i in issues], ensure_ascii=False, indent=2)
    _write_or_print(output, args.output)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    report = ReportAgent().summarize_csv(args.result_csv, top_n=args.top_n)
    _write_or_print(report, args.output)
    return 0


def _write_or_print(content: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"written: {path}")
    else:
        print(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dq-agent",
        description="Data Quality Inspection Agent for Hive data warehouse",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Build rule plan from table metadata")
    p_plan.add_argument("--metadata", required=True, help="YAML metadata path")
    p_plan.add_argument("--output", help="Output JSON path")
    p_plan.set_defaults(func=cmd_plan)

    p_gen = sub.add_parser("generate", help="Generate HiveSQL from metadata")
    p_gen.add_argument("--metadata", required=True, help="YAML metadata path")
    p_gen.add_argument("--biz-date", default=None, help="Business date, e.g. 2026-05-09 or ${biz_date}")
    p_gen.add_argument("--quality-table", default="dqc_check_result", help="Hive quality result table")
    p_gen.add_argument("--code-table", default="dim_standard_code", help="Hive standard code table")
    p_gen.add_argument("--output", help="Output SQL path")
    p_gen.set_defaults(func=cmd_generate)

    p_review = sub.add_parser("review", help="Review generated HiveSQL")
    p_review.add_argument("--sql", required=True, help="Generated SQL path")
    p_review.add_argument("--metadata", help="Optional metadata path for partition checking")
    p_review.add_argument("--output", help="Output JSON path")
    p_review.set_defaults(func=cmd_review)

    p_report = sub.add_parser("report", help="Summarize DQ result CSV")
    p_report.add_argument("--result-csv", required=True, help="CSV exported from result table")
    p_report.add_argument("--top-n", type=int, default=10, help="Top N fields in summary")
    p_report.add_argument("--output", help="Output markdown path")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - CLI needs concise error output
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
