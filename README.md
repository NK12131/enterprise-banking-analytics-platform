<div align="center">

# 🏦 Enterprise Banking Analytics Platform

### End-to-End Banking Analytics Platform using Snowflake, Python, Apache Airflow, AWS S3 & Tableau

[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![Apache Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white)]()
[![AWS S3](https://img.shields.io/badge/AWS_S3-569A31?style=for-the-badge&logo=amazonaws&logoColor=white)]()
[![Terraform](https://img.shields.io/badge/Terraform-623CE4?style=for-the-badge&logo=terraform&logoColor=white)]()
[![Tableau](https://img.shields.io/badge/Tableau-E97627?style=for-the-badge&logo=tableau&logoColor=white)]()
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)]()

---

Enterprise-grade Banking Analytics Platform demonstrating modern Data Engineering best practices using Snowflake's cloud-native ecosystem.

Built using a layered RAW → STAGING → CORE → GOLD architecture with Snowflake, Apache Airflow, Snowpipe, AWS S3, Python,SQL and Tableau. The project demonstrates automated ingestion, incremental processing, data quality validation, dimensional modeling, and analytics-ready reporting.

</div>

---

# 📖 Project Overview

Financial institutions process millions of transactions daily across customer accounts, digital banking channels, loans, credit cards, and fraud detection systems. This project demonstrates how an enterprise banking organization can build a scalable, cloud-native analytics platform that automates data ingestion, transformation, validation, and reporting using Snowflake's cloud ecosystem.

The platform implements a layered RAW → STAGING → CORE → GOLD architecture. Daily banking data is generated, uploaded to Amazon S3, automatically ingested into Snowflake using Snowpipe, transformed into dimensional models, validated through multiple quality gates, and delivered as business-ready analytics for executive dashboards.

Key capabilities include:

- Automated Snowpipe ingestion
- Incremental ETL processing
- SCD Type 2 dimensions
- Enterprise star schema
- Data quality validation
- Apache Airflow orchestration
- Executive analytics dashboards

---

# 🎯 Business Objectives

- Build a scalable cloud-native banking analytics platform
- Automate ingestion using Snowpipe
- Implement incremental ELT pipelines
- Build dimensional models using Snowflake
- Implement SCD Type 2 dimensions
- Perform layered data quality validation
- Orchestrate workflows with Apache Airflow
- Deliver analytics-ready Gold marts
- Visualize KPIs using Tableau
- Demonstrate production-ready cloud data engineering practices

---

# 🏗 Solution Architecture

```text
               Banking Data Generators
                        │
                        ▼
                 Daily Parquet Files
                        │
                        ▼
                  Amazon S3 Bucket
                        │
                        ▼
              Snowpipe Auto Ingestion
                        │
                        ▼
                  RAW Snowflake Layer
                        │
                        ▼
                STAGING Transformations
                        │
                        ▼
               CORE Data Warehouse
        ├── Customer Dimension (SCD2)
        ├── Account Dimension (SCD2)
        ├── Transaction Fact
        ├── Fraud Fact
        ├── Loan Fact
        └── Credit Card Fact
                        │
                        ▼
                GOLD Analytics Layer
        ├── Customer 360
        ├── Branch Performance
        ├── Fraud Analytics
        └── Executive KPI
                        │
                        ▼
            Tableau Executive Dashboards
```

---

# 🏛 Data Architecture

## Raw

Landing layer storing data automatically ingested by Snowpipe.

Contains:

- Transactions (Parquet)
- Fraud Events (JSON)

---

## Staging

Business validation and cleansing.

Examples:

- Data standardization
- Duplicate removal
- Data quality validation
- Data enrichment
- Business rule enforcement

---

## Core

Enterprise dimensional warehouse.

Dimensions:

- DIM_CUSTOMER (SCD Type 2)
- DIM_ACCOUNT (SCD Type 2)

Facts:

- FACT_TRANSACTIONS
- FACT_FRAUD
- FACT_LOANS
- FACT_CREDIT_CARDS

---

## Gold

Business-ready analytical marts.

Includes:

- Customer 360
- Branch Performance
- Fraud Analytics
- Executive KPI

---

# 🚀 Technology Stack

| Category       | Technology        |
| -------------- | ----------------- |
| Cloud Storage  | AWS S3            |
| Data Warehouse | Snowflake         |
| Programming    | Python            |
| Orchestration  | Apache Airflow    |
| Infrastructure | Terraform         |
| Scheduling     | Snowflake Tasks   |
| CDC            | Snowflake Streams |
| Automation     | Snowpipe          |
| Dashboard      | Tableau           |
| SQL            | Snowflake SQL     |
| CI/CD          | GitHub Actions    |

---

# 📂 Project Structure

```text
                enterprise-banking-analytics-platform/

                ├── airflow/
                │   └── banking_daily_incremental.py
                │
                ├── generators/
                │   ├── transactions/
                │   └── fraud/
                │
                ├── ingestion/
                │   └── s3/
                │
                ├── snowflake/
                │   ├── 01_database/
                │   ├── 02_storage/
                │   ├── 03_raw_tables/
                │   ├── 04_pipes/
                │   ├── 05_monitoring/
                │   ├── 06_staging/
                │   ├── 07_core/
                │   └── 08_gold/
                │
                ├── dbt/
                ├── dashboards/
                ├── images/
                ├── .github/
                ├── requirements.txt
                └── README.md
```

---

# ⚡ Pipeline Workflow

```
                Generate Transactions
                        │
                        ▼
                Generate Fraud
                        │
                        ▼
                Validate Parquet
                        │
                        ▼
                Snowpipe Health Check
                        │
                        ▼
                Upload to S3
                        │
                        ▼
                Wait for Snowpipe
                        │
                        ▼
                RAW Validation
                        │
                        ▼
                STAGING Validation
                        │
                        ▼
                Merge Transaction Fact
                        │
                        ▼
                Merge Fraud Fact
                        │
                        ▼
                Customer SCD2
                        │
                        ▼
                Account SCD2
                        │
                        ▼
                ┌──────────────┐
                │              │
                ▼              ▼
            Loan Fact      Credit Card Fact
                │              │
                └───────┬──────┘
                        ▼
                 Core Validation
                        │
                        ▼
                Customer 360
                        │
                        ▼
                Branch Performance
                        │
                        ▼
                Fraud Analytics
                        │
                        ▼
                Executive KPI
                        │
                        ▼
                Gold Validation
                        │
                        ▼
                Pipeline Audit

```

# 📊 Gold Analytics Layer

    Customer 360
        - Customer profile
        - Transaction summary
        - Fraud history
        - Loan summary
        - Credit card usage
    Branch Performance
        - Revenue
        - Deposits
        - Withdrawals
        - Transaction volume
    Fraud Analytics
        - Fraud rate
        - Risk score analysis
        - Fraud by branch
        - Fraud trends
    Executive KPI
        - Total transactions
        - Revenue
        - Active customers
        - Fraud percentage
        - Loan portfolio
        - Credit card portfolio

---

# 🧪 Data Quality

Validation rules include:

- Snowpipe ingestion validation
- RAW row count verification
- Null checks
- Duplicate detection
- Invalid transaction amount validation
- Fraud risk score validation
- Incremental fact validation
- Gold KPI validation

---

# ⚙️ Production Features

- Incremental ETL processing
- Snowpipe automated ingestion
- SCD Type 2 dimensions
- Enterprise star schema
- Apache Airflow orchestration
- Idempotent pipeline design
- Pipeline audit logging
- Layered data quality validation
- Parallel fact processing
- Gold analytics marts

---

# 📈 Analytics Dashboards

- Executive KPI Dashboard
- Customer 360 Dashboard
- Branch Performance Dashboard
- Fraud Analytics Dashboard

---

# 📋 Future Enhancements

- Snowpipe Streaming
- Kafka real-time ingestion
- Snowflake Cortex AI
- Data Catalog Integration
- Great Expectations
- OpenTelemetry Monitoring

---

# 📚 Skills Demonstrated

- Data Engineering
- Cloud Data Warehousing
- Snowflake
- Snowflake SQL
- Snowpipe
- SQL
- Python
- Apache Airflow
- Star Schema Design
- Slowly Changing Dimensions (Type 2)
- Terraform
- CI/CD
- Data Quality
- Data Modeling
- Incremental Processing
- Enterprise Architecture


## 👤 Author

**Nithin Kumar**
