# 数据质量巡检 Agent（Hive 数仓版）

这是一个可落地的「数据质量巡检 Agent」示例项目，面向 Hive 离线数仓 / DolphinScheduler 调度场景。

它可以根据表元数据自动规划数据质量规则，生成 HiveSQL，并对 SQL 做基础风险审查。

## 能力

- 自动识别字段校验规则：
  - 非空校验 `NOT_NULL`
  - 标准码表值域校验 `ENUM_CODE`
  - 主键唯一性校验 `UNIQUE_KEY`
  - 金额/费用字段非负校验 `NON_NEGATIVE`
  - 日期时间字段未来值校验 `FUTURE_DATE`
  - 分区空数据校验 `PARTITION_NOT_EMPTY`
- 自动生成 HiveSQL，结果统一写入质量结果表。
- 自动补充分区条件，避免默认全表扫描。
- 支持人工在 YAML 中追加自定义规则。
- 可接入 DolphinScheduler，作为普通 Shell/Hive SQL 任务执行。

## 目录结构

```text
dq_quality_agent/
  src/dq_agent/
    cli.py                 # 命令行入口
    models.py              # 数据模型
    metadata_loader.py     # 元数据加载
    agents/
      planner.py           # 规则规划 Agent
      sql_generator.py     # HiveSQL 生成 Agent
      reviewer.py          # SQL 审查 Agent
      report_agent.py      # 巡检摘要 Agent
  examples/tables/         # 示例表元数据
  scripts/                 # 建表 SQL、调度脚本
  tests/                   # 单元测试
```

## 快速开始

### 1. 安装依赖

```bash
cd dq_quality_agent
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 生成规则计划

```bash
python -m dq_agent.cli plan \
  --metadata examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml \
  --output output/rule_plan.json
```

### 3. 生成 HiveSQL

```bash
python -m dq_agent.cli generate \
  --metadata examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml \
  --biz-date '${biz_date}' \
  --output output/dq_check.sql
```

### 4. 审查 SQL

```bash
python -m dq_agent.cli review --sql output/dq_check.sql
```

### 5. 在 Hive 执行

先建结果表：

```bash
hive -f scripts/init_quality_result_table.sql
```

再执行生成的巡检 SQL：

```bash
hive -hivevar biz_date=2026-05-09 -f output/dq_check.sql
```

或者在 DolphinScheduler Shell 节点中：

```bash
python -m dq_agent.cli generate \
  --metadata examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml \
  --biz-date '${biz_date}' \
  --output /tmp/dq_check_${biz_date}.sql

hive -hivevar biz_date=${biz_date} -f /tmp/dq_check_${biz_date}.sql
```

## 表元数据 YAML 示例

```yaml
database: ads
table_name: ads_medr_inpatient_patient_fy_info_d_i
partition_column: dt
partition_value: "${biz_date}"
primary_keys:
  - organiz_code
  - inpatient_no
  - settlement_id
  - charge_id
columns:
  - name: charge_type
    type: string
    comment: 费用项目类型
    nullable: false
    standard_encode: FEE_ITEM
```

## 自定义规则

可以在 YAML 中配置：

```yaml
manual_rules:
  - rule_type: CUSTOM_SQL
    rule_id: total_fee_should_equal_item_fee_sum
    field_name: total_fee
    severity: HIGH
    expression: "abs(nvl(t.total_fee,0) - nvl(t.item_fee,0)) > 0.01"
    reason: "总费用和明细费用不一致"
```

`expression` 会被拼到 `WHERE` 后面，表别名固定为 `t`。

## 结果表字段

生成的 SQL 会写入 `dqc_check_result`，字段包括：

- `rule_id`
- `table_name`
- `rule_type`
- `field_name`
- `field_value`
- `biz_key`
- `error_reason`
- `severity`
- `check_time`
- 分区字段 `dt`

## 说明

这是工程化骨架，不依赖具体公司的元数据系统。真实落地时可以把 `metadata_loader.py` 改成读取 Hive Metastore、Atlas、DataHub、内部码表系统或 Excel 配置。
