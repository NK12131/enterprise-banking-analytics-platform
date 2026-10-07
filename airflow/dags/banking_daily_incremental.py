"""
Enterprise Banking Analytics Platform.

Daily incremental Airflow pipeline.

Pipeline
--------
Daily Transactions
    -> Daily Fraud
    -> Validate Parquet
    -> Upload S3
    -> Wait for Snowpipe
    -> Validate RAW
    -> Validate STAGING
"""

from __future__ import annotations

from datetime import timedelta

import pendulum

import json

from airflow import DAG

from airflow.operators.python import PythonOperator

from airflow.operators.bash import BashOperator

from airflow.providers.snowflake.hooks.snowflake import (
    SnowflakeHook,
)

from airflow.providers.snowflake.operators.snowflake import (
    SnowflakeCheckOperator,
)

from airflow.providers.common.sql.operators.sql import (
    SQLCheckOperator,
    SQLExecuteQueryOperator,
)


# =====================================================================
# Configuration
# =====================================================================

PROJECT_DIR = (
    "/opt/airflow/"
    "enterprise-banking-analytics-platform"
)

SNOWFLAKE_CONN_ID = "snowflake_banking"


DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(
        minutes=5,
    ),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(
        minutes=30,
    ),
}


# =====================================================================
# Snowpipe ingestion check
# =====================================================================

def wait_for_snowpipe(
    **context,
) -> None:
    """
    Validate execution-date files were loaded
    by Snowpipe.
    """

    execution_date = context["ds"]

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    sql = """
        SELECT
            COUNT_IF(
                TABLE_NAME = 'RAW_TRANSACTIONS'
                AND FILE_NAME LIKE %s
            ) AS TRANSACTION_FILES,

            COUNT_IF(
                TABLE_NAME = 'RAW_FRAUD'
                AND FILE_NAME LIKE %s
            ) AS FRAUD_FILES

        FROM TABLE(
            ENTERPRISE_BANKING
            .INFORMATION_SCHEMA
            .COPY_HISTORY(
                START_TIME =>
                    DATEADD(
                        'HOUR',
                        -24,
                        CURRENT_TIMESTAMP()
                    )
            )
        )

        WHERE STATUS = 'Loaded'
    """

    transaction_pattern = (
        f"%transaction_date="
        f"{execution_date}/%"
    )

    fraud_pattern = (
        f"%detection_date="
        f"{execution_date}/%"
    )

    result = hook.get_first(
        sql=sql,
        parameters=(
            transaction_pattern,
            fraud_pattern,
        ),
    )

    transaction_files = int(
        result[0] or 0
    )

    fraud_files = int(
        result[1] or 0
    )

    print(
        "Snowpipe load status | "
        f"execution_date={execution_date} | "
        f"transaction_files={transaction_files} | "
        f"fraud_files={fraud_files}"
    )

    if transaction_files <= 0:
        raise RuntimeError(
            "Transaction partition has not "
            "completed Snowpipe ingestion."
        )

    if fraud_files <= 0:
        raise RuntimeError(
            "Fraud partition has not "
            "completed Snowpipe ingestion."
        )

    print(
        "Snowpipe ingestion completed | "
        f"execution_date={execution_date}"
    )

# =====================================================================
# Snowpipe health check
# =====================================================================

def check_snowpipe_health() -> None:
    """
    Validate required Snowpipes are running.

    Fail before S3 upload when a pipe is paused
    or unavailable.
    """

    hook = SnowflakeHook(
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
    )

    pipes = (
        (
            "TRANSACTIONS",
            (
                "ENTERPRISE_BANKING."
                "RAW.PIPE_TRANSACTIONS"
            ),
        ),
        (
            "FRAUD",
            (
                "ENTERPRISE_BANKING."
                "RAW.PIPE_FRAUD"
            ),
        ),
    )

    unhealthy_pipes: list[str] = []

    for pipe_name, pipe_path in pipes:

        sql = f"""
            SELECT SYSTEM$PIPE_STATUS(
                '{pipe_path}'
            )
        """

        result = hook.get_first(sql=sql)

        if not result or not result[0]:
            raise RuntimeError(
                "Unable to retrieve Snowpipe status: "
                f"{pipe_path}"
            )

        status = json.loads(result[0])

        execution_state = status.get(
            "executionState",
            "UNKNOWN",
        )

        print(
            "Snowpipe status | "
            f"pipe={pipe_name} | "
            f"state={execution_state}"
        )

        if execution_state != "RUNNING":
            unhealthy_pipes.append(
                f"{pipe_name}={execution_state}"
            )

    if unhealthy_pipes:
        raise RuntimeError(
            "Snowpipe pre-flight failed | "
            + ", ".join(unhealthy_pipes)
        )

    print(
        "Snowpipe pre-flight completed | "
        "all required pipes are RUNNING"
    )

merge_fact_transactions = SQLExecuteQueryOperator(
    task_id="merge_fact_transactions",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="04_merge_fact_transactions.sql",
    execution_timeout=timedelta(minutes=30)
)

merge_fact_fraud = SQLExecuteQueryOperator(
    task_id="merge_fact_fraud",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="05_merge_fact_fraud.sql",
    execution_timeout=timedelta(minutes=30)
)

validate_core_incremental = SQLCheckOperator(
    task_id="validate_core_incremental",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="08_validate_core_incremental.sql",
)


log_pipeline_audit = SQLExecuteQueryOperator(
    task_id="log_pipeline_audit",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="09_log_pipeline_audit.sql",
    trigger_rule="all_done",
)

process_dim_customer_scd2 = SQLExecuteQueryOperator(
    task_id="process_dim_customer_scd2",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="14_process_dim_customer_scd2.sql",
)

validate_dim_customer = SQLCheckOperator(
    task_id="validate_dim_customer",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="15_validate_dim_customer.sql",
    execution_timeout=timedelta(minutes=30)
)

process_dim_account_scd2 = SQLExecuteQueryOperator(
    task_id="process_dim_account_scd2",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="23_process_dim_account.sql",
)

validate_dim_account = SQLCheckOperator(
    task_id="validate_dim_account",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="22_validate_dim_account.sql",
    execution_timeout=timedelta(minutes=30)
)

process_fact_loans = SQLExecuteQueryOperator(
    task_id="process_fact_loans",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="35_process_fact_loans.sql",
    execution_timeout=timedelta(minutes=30)
)

validate_fact_loans = SQLCheckOperator(
    task_id="validate_fact_loans",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="32_validate_fact_loans.sql",
)

# =====================================================================
# GOLD Layer
# =====================================================================

load_customer360 = SQLExecuteQueryOperator(
    task_id="load_customer360",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="GOLD",
    sql="02_load_mart_customer_360.sql",
)

load_branch_performance = SQLExecuteQueryOperator(
    task_id="load_branch_performance",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="GOLD",
    sql="04_load_mart_branch_performance.sql",
)

load_fraud_analytics = SQLExecuteQueryOperator(
    task_id="load_fraud_analytics",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="GOLD",
    sql="06_load_mart_fraud_analytics.sql",
)

load_executive_kpi = SQLExecuteQueryOperator(
    task_id="load_executive_kpi",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="GOLD",
    sql="08_load_mart_executive_kpi.sql",
)

validate_gold = SQLCheckOperator(
    task_id="validate_gold",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="GOLD",
    sql="10_validate_gold.sql",
)

process_fact_credit_cards = SQLExecuteQueryOperator(
    task_id="process_fact_credit_cards",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="37_process_fact_credit_cards.sql",
    execution_timeout=timedelta(minutes=30)
)

validate_fact_credit_cards = SQLCheckOperator(
    task_id="validate_fact_credit_cards",
    conn_id=SNOWFLAKE_CONN_ID,
    database="ENTERPRISE_BANKING",
    schema="CORE",
    sql="38_validate_fact_credit_cards.sql",
)

# =====================================================================
# DAG
# =====================================================================


with DAG(
    dag_id="banking_daily_incremental",
    description=(
        "Daily incremental banking pipeline "
        "for transactions and fraud"
    ),
    start_date=pendulum.datetime(
        2026,
        7,
        15,
        tz="UTC",
    ),
    schedule="0 2 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    template_searchpath=[
            f"{PROJECT_DIR}/snowflake/07_core",
            f"{PROJECT_DIR}/snowflake/08_gold",    
    ],
    tags=[
        "banking",
        "incremental",
        "snowflake",
        "aws",
        "snowpipe",
    ],
    email_on_failure=False
) as dag:

    # =================================================================
    # Daily transaction generation
    # =================================================================

    generate_daily_transactions = BashOperator(
        task_id="generate_daily_transactions",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m "
            "generators.transactions."
            "daily_transaction_generator "
            "--execution-date {{ ds }}"
        ),
        execution_timeout=timedelta(
            hours=2,
        ),
    )

    # =================================================================
    # Daily fraud generation
    # =================================================================

    generate_daily_fraud = BashOperator(
        task_id="generate_daily_fraud",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m "
            "generators.fraud."
            "daily_fraud_generator "
            "--execution-date {{ ds }}"
        ),
        execution_timeout=timedelta(
            minutes=60,
        ),
    )

    # =================================================================
    # Daily Parquet validation
    # =================================================================

    validate_daily_parquet = BashOperator(
        task_id="validate_daily_parquet",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m "
            "scripts.validate_daily_parquet "
            "--execution-date {{ ds }}"
        ),
    )

    # =================================================================
    # Check snowpipe health
    # =================================================================

    check_snowpipe_health_task = PythonOperator(
        task_id="check_snowpipe_health",
        python_callable=check_snowpipe_health,
        retries=2,
        retry_delay=timedelta(
            minutes=5,
        ),
        execution_timeout=timedelta(
            minutes=5,
        ),
    )

    # =================================================================
    # Upload daily partitions
    # =================================================================

    upload_daily_s3 = BashOperator(
        task_id="upload_daily_s3",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m "
            "ingestion.s3.s3_uploader "
            "--mode daily "
            "--execution-date {{ ds }}"
        ),
        execution_timeout=timedelta(
            hours=1,
        ),
    )

    # =================================================================
    # Snowpipe ingestion wait
    # =================================================================

    wait_for_snowpipe_ingestion = PythonOperator(
        task_id="wait_for_snowpipe_ingestion",
        python_callable=wait_for_snowpipe,
        execution_timeout=timedelta(
            minutes=10,
        ),
        retries=12,
        retry_delay=timedelta(
            minutes=5,
        ),
        retry_exponential_backoff=False,
    )

    # =================================================================
    # RAW data quality gate
    # =================================================================

    validate_daily_raw = SnowflakeCheckOperator(
        task_id="validate_daily_raw",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        database="ENTERPRISE_BANKING",
        schema="RAW",
        sql="""
            SELECT
                COUNT(*) > 0
            FROM RAW_TRANSACTIONS
            WHERE SOURCE_FILE LIKE
                '%transaction_date={{ ds }}/%'
        """,
    )

    # =================================================================
    # STAGING transaction quality gate
    # =================================================================

    validate_daily_transactions = (
        SnowflakeCheckOperator(
            task_id=(
                "validate_daily_transactions"
            ),
            snowflake_conn_id=(
                SNOWFLAKE_CONN_ID
            ),
            database="ENTERPRISE_BANKING",
            schema="STAGING",
            sql="""
                SELECT
                    COUNT(*) > 0
                    AND
                    COUNT_IF(
                        TRANSACTION_ID IS NULL
                    ) = 0
                    AND
                    COUNT_IF(
                        TRANSACTION_TIMESTAMP
                        IS NULL
                    ) = 0
                    AND
                    COUNT_IF(
                        TRANSACTION_AMOUNT <= 0
                    ) = 0
                FROM STG_TRANSACTIONS
                WHERE SOURCE_FILE LIKE
                    '%transaction_date={{ ds }}/%'
            """,
        )
    )

    # =================================================================
    # STAGING fraud quality gate
    # =================================================================

    validate_daily_fraud = SnowflakeCheckOperator(
        task_id="validate_daily_fraud",
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        database="ENTERPRISE_BANKING",
        schema="STAGING",
        sql="""
            SELECT
                COUNT(*) > 0
                AND
                COUNT_IF(
                    FRAUD_CASE_ID IS NULL
                ) = 0
                AND
                COUNT_IF(
                    RISK_SCORE < 0
                    OR RISK_SCORE > 100
                ) = 0
            FROM STG_FRAUD
            WHERE SOURCE_FILE LIKE
                '%detection_date={{ ds }}/%'
        """,
    )

    # =================================================================
# Dependencies
# =================================================================

# -----------------------------------------------------------------
# File Generation -> Ingestion
# -----------------------------------------------------------------

(
    generate_daily_transactions
    >> generate_daily_fraud
    >> validate_daily_parquet
    >> check_snowpipe_health_task
    >> upload_daily_s3
    >> wait_for_snowpipe_ingestion
    >> validate_daily_raw
)

# -----------------------------------------------------------------
# RAW -> STAGING Validation
# -----------------------------------------------------------------

validate_daily_raw >> [
    validate_daily_transactions,
    validate_daily_fraud,
]

# -----------------------------------------------------------------
# STAGING -> CORE Facts
# -----------------------------------------------------------------

validate_daily_transactions >> merge_fact_transactions

validate_daily_fraud >> merge_fact_fraud

# -----------------------------------------------------------------
# FACTS -> CUSTOMER DIMENSION
# -----------------------------------------------------------------

[
    merge_fact_transactions,
    merge_fact_fraud,
] >> process_dim_customer_scd2

process_dim_customer_scd2 >> validate_dim_customer

# -----------------------------------------------------------------
# CUSTOMER -> ACCOUNT DIMENSION
# -----------------------------------------------------------------

validate_dim_customer >> process_dim_account_scd2

process_dim_account_scd2 >> validate_dim_account

# -----------------------------------------------------------------
# ACCOUNT -> FACT PROCESSING
# -----------------------------------------------------------------

validate_dim_account >> [
    process_fact_loans,
    process_fact_credit_cards,
]

# -----------------------------------------------------------------
# FACT VALIDATION
# -----------------------------------------------------------------

process_fact_loans >> validate_fact_loans

process_fact_credit_cards >> validate_fact_credit_cards

# -----------------------------------------------------------------
# CORE VALIDATION
# -----------------------------------------------------------------

[
    validate_fact_loans,
    validate_fact_credit_cards,
] >> validate_core_incremental

# -----------------------------------------------------------------
# GOLD LAYER
# -----------------------------------------------------------------

validate_core_incremental \
>> load_customer360 \
>> load_branch_performance \
>> load_fraud_analytics \
>> load_executive_kpi \
>> validate_gold \
>> log_pipeline_audit