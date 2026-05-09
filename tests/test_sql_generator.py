from dq_agent.agents.planner import PlannerAgent
from dq_agent.agents.sql_generator import HiveSqlGeneratorAgent
from dq_agent.metadata_loader import MetadataLoader


def test_generator_contains_partition_filter():
    table = MetadataLoader.load_yaml("examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml")
    plans = PlannerAgent().build_plan(table)
    sql = HiveSqlGeneratorAgent().generate(table, plans, biz_date="2026-05-09")

    assert "WHERE dt = '2026-05-09'" in sql
    assert "valid_code_fee_item" in sql
    assert "INSERT OVERWRITE TABLE dqc_check_result" in sql


def test_generator_does_not_use_select_star():
    table = MetadataLoader.load_yaml("examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml")
    plans = PlannerAgent().build_plan(table)
    sql = HiveSqlGeneratorAgent().generate(table, plans, biz_date="2026-05-09")

    assert "SELECT *" not in sql.upper()
