/*****************************************************************************************
 Script Name : 11_create_dynamic_tables.sql
******************************************************************************************/

CREATE OR REPLACE DYNAMIC TABLE GOLD.DT_CUSTOMER_SUMMARY
TARGET_LAG='5 MINUTES'
WAREHOUSE=WH_TRANSFORM
AS
SELECT
    customer_id,
    customer_name,
    total_balance,
    risk_rating
FROM GOLD.MART_CUSTOMER_PROFITABILITY;