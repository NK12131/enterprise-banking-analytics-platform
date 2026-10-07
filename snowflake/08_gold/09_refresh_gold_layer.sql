USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA GOLD;

-- Customer 360
TRUNCATE TABLE MART_CUSTOMER_360;
!source 02_load_mart_customer_360.sql

-- Branch Performance
TRUNCATE TABLE MART_BRANCH_PERFORMANCE;
!source 04_load_mart_branch_performance.sql

-- Fraud Analytics
TRUNCATE TABLE MART_FRAUD_ANALYTICS;
!source 06_load_mart_fraud_analytics.sql

-- Executive KPI
TRUNCATE TABLE MART_EXECUTIVE_KPI;
!source 08_load_mart_executive_kpi.sql