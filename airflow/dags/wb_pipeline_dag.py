"""
World Bank Indicators Pipeline DAG

Runs daily at 06:00 UTC. WB data is annual but corrections appear throughout the year,
so daily runs ensure we pick up revisions. Full historical backfill via catchup=True.
"""

import logging
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.email import send_email

logger = logging.getLogger(__name__)

REPO_ROOT = "/opt/airflow"
DBT_DIR = f"{REPO_ROOT}/dbt_project"

_COMMON_ENV = {
    "S3_BUCKET": os.environ.get("S3_BUCKET", ""),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", ""),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
    "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
    "SNOWFLAKE_ACCOUNT": os.environ.get("SNOWFLAKE_ACCOUNT", ""),
    "SNOWFLAKE_USER": os.environ.get("SNOWFLAKE_USER", ""),
    "SNOWFLAKE_PASSWORD": os.environ.get("SNOWFLAKE_PASSWORD", ""),
    "SNOWFLAKE_ROLE": os.environ.get("SNOWFLAKE_ROLE", "TRANSFORMER"),
    "SNOWFLAKE_DATABASE": os.environ.get("SNOWFLAKE_DATABASE", "WB_WAREHOUSE"),
    "SNOWFLAKE_WAREHOUSE": os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
}


def _on_failure(context):
    task_id = context["task_instance"].task_id
    dag_id = context["dag"].dag_id
    exec_date = context["execution_date"]
    logger.error("task_failed dag=%s task=%s date=%s", dag_id, task_id, exec_date)

    alert_email = os.environ.get("ALERT_EMAIL")
    if alert_email:
        send_email(
            to=alert_email,
            subject=f"[AIRFLOW FAILURE] {dag_id} / {task_id}",
            html_content=f"<b>Task</b> {task_id} failed on {exec_date}",
        )


default_args = {
    "owner": "sachin",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=10),
    "on_failure_callback": _on_failure,
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="wb_indicators_pipeline",
    description="Daily World Bank indicator ingest -> Snowflake -> dbt",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=True,
    max_active_runs=1,
    default_args=default_args,
    tags=["world-bank", "indicators", "snowflake"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_wb_indicators",
        bash_command=f"cd {REPO_ROOT} && python -m ingestion.main --run-date {{{{ ds }}}}",
        env={**_COMMON_ENV, "RUN_DATE": "{{ ds }}"},
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --target prod",
        env=_COMMON_ENV,
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"cd {DBT_DIR} && dbt snapshot --target prod",
        env=_COMMON_ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --target prod",
        env=_COMMON_ENV,
    )

    ingest >> dbt_run >> dbt_snapshot >> dbt_test
