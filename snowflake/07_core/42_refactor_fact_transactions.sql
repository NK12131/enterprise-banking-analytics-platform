USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

-------------------------------------------------------------------------------
-- Add surrogate key columns
-------------------------------------------------------------------------------

ALTER TABLE FACT_TRANSACTIONS
ADD COLUMN IF NOT EXISTS CUSTOMER_KEY NUMBER;

ALTER TABLE FACT_TRANSACTIONS
ADD COLUMN IF NOT EXISTS ACCOUNT_KEY NUMBER;

ALTER TABLE FACT_TRANSACTIONS
ADD COLUMN IF NOT EXISTS BRANCH_KEY NUMBER;

ALTER TABLE FACT_TRANSACTIONS
ADD COLUMN IF NOT EXISTS MERCHANT_KEY NUMBER;

ALTER TABLE FACT_TRANSACTIONS
ADD COLUMN IF NOT EXISTS DATE_KEY NUMBER;

-------------------------------------------------------------------------------
-- Populate CUSTOMER_KEY
-------------------------------------------------------------------------------

UPDATE FACT_TRANSACTIONS T
SET CUSTOMER_KEY = D.CUSTOMER_KEY
FROM DIM_CUSTOMER D
WHERE T.CUSTOMER_ID = D.CUSTOMER_ID
  AND D.IS_CURRENT = TRUE
  AND T.CUSTOMER_KEY IS NULL;

-------------------------------------------------------------------------------
-- Populate ACCOUNT_KEY
-------------------------------------------------------------------------------

UPDATE FACT_TRANSACTIONS T
SET ACCOUNT_KEY = D.ACCOUNT_KEY
FROM DIM_ACCOUNT D
WHERE T.ACCOUNT_ID = D.ACCOUNT_ID
  AND D.IS_CURRENT = TRUE
  AND T.ACCOUNT_KEY IS NULL;

-------------------------------------------------------------------------------
-- Populate BRANCH_KEY
-------------------------------------------------------------------------------

UPDATE FACT_TRANSACTIONS T
SET BRANCH_KEY = D.BRANCH_KEY
FROM DIM_BRANCH D
WHERE T.BRANCH_ID = D.BRANCH_ID
  AND T.BRANCH_KEY IS NULL;

-------------------------------------------------------------------------------
-- Populate DATE_KEY
-------------------------------------------------------------------------------

UPDATE FACT_TRANSACTIONS T
SET DATE_KEY = D.DATE_KEY
FROM DIM_DATE D
WHERE T.TRANSACTION_DATE = D.FULL_DATE
  AND T.DATE_KEY IS NULL;

-------------------------------------------------------------------------------
-- Populate MERCHANT_KEY
-------------------------------------------------------------------------------

UPDATE FACT_TRANSACTIONS T
SET MERCHANT_KEY = D.MERCHANT_KEY
FROM DIM_MERCHANT D
WHERE T.MERCHANT_NAME = D.MERCHANT_NAME
  AND T.MERCHANT_CATEGORY = D.MERCHANT_CATEGORY
  AND T.TRANSACTION_CITY = D.MERCHANT_CITY
  AND T.TRANSACTION_STATE = D.MERCHANT_STATE
  AND T.MERCHANT_KEY IS NULL;

