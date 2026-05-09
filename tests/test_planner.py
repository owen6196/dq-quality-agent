from dq_agent.agents.planner import PlannerAgent
from dq_agent.metadata_loader import MetadataLoader


def test_planner_builds_expected_rules():
    table = MetadataLoader.load_yaml("examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml")
    plans = PlannerAgent().build_plan(table)
    rule_types = {p.rule_type for p in plans}

    assert "PARTITION_NOT_EMPTY" in rule_types
    assert "UNIQUE_KEY" in rule_types
    assert "NOT_NULL" in rule_types
    assert "ENUM_CODE" in rule_types
    assert "NON_NEGATIVE" in rule_types


def test_planner_contains_charge_type_enum_rule():
    table = MetadataLoader.load_yaml("examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml")
    plans = PlannerAgent().build_plan(table)

    enum_rules = [p for p in plans if p.rule_type == "ENUM_CODE" and p.field_name == "charge_type"]
    assert len(enum_rules) == 1
    assert enum_rules[0].standard_encode == "FEE_ITEM"
