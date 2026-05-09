CREATE TABLE IF NOT EXISTS dqc_check_result (
  rule_id      STRING COMMENT '规则ID',
  table_name   STRING COMMENT '表名',
  rule_type    STRING COMMENT '规则类型',
  field_name   STRING COMMENT '字段名',
  field_value  STRING COMMENT '异常字段值',
  biz_key      STRING COMMENT '业务主键',
  error_reason STRING COMMENT '异常原因',
  severity     STRING COMMENT '严重等级: LOW/MEDIUM/HIGH/CRITICAL',
  check_time   TIMESTAMP COMMENT '检查时间'
)
COMMENT '数据质量巡检结果表'
PARTITIONED BY (dt STRING COMMENT '业务日期')
STORED AS ORC;
