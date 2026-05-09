#!/usr/bin/env bash
set -euo pipefail

BIZ_DATE=${biz_date:-$(date -d "yesterday" +%F)}
PROJECT_HOME=/opt/dq_quality_agent
SQL_FILE=/tmp/dq_check_${BIZ_DATE}.sql

cd "${PROJECT_HOME}"

python -m dq_agent.cli generate \
  --metadata examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml \
  --biz-date "${BIZ_DATE}" \
  --output "${SQL_FILE}"

python -m dq_agent.cli review \
  --metadata examples/tables/ads_medr_inpatient_patient_fy_info_d_i.yaml \
  --sql "${SQL_FILE}"

hive -hivevar biz_date="${BIZ_DATE}" -f "${SQL_FILE}"
