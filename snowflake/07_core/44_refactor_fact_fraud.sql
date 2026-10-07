USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

------------------------------------------------------------------------------
-- Add Conformed Dimension Keys
------------------------------------------------------------------------------

ALTER TABLE FACT_FRAUD
ADD COLUMN IF NOT EXISTS CUSTOMER_KEY NUMBER;

ALTER TABLE FACT_FRAUD
ADD COLUMN IF NOT EXISTS ACCOUNT_KEY NUMBER;

ALTER TABLE FACT_FRAUD
ADD COLUMN IF NOT EXISTS BRANCH_KEY NUMBER;

ALTER TABLE FACT_FRAUD
ADD COLUMN IF NOT EXISTS DATE_KEY NUMBER;

ALTER TABLE FACT_FRAUD
ADD COLUMN IF NOT EXISTS MERCHANT_KEY NUMBER;

------------------------------------------------------------------------------
-- CUSTOMER_KEY
------------------------------------------------------------------------------

UPDATE FACT_FRAUD F
SET CUSTOMER_KEY = D.CUSTOMER_KEY
FROM DIM_CUSTOMER D
WHERE F.CUSTOMER_ID = D.CUSTOMER_ID
  AND D.IS_CURRENT = TRUE
  AND F.CUSTOMER_KEY IS NULL;

------------------------------------------------------------------------------
-- ACCOUNT_KEY
------------------------------------------------------------------------------

UPDATE FACT_FRAUD F
SET ACCOUNT_KEY = D.ACCOUNT_KEY
FROM DIM_ACCOUNT D
WHERE F.ACCOUNT_ID = D.ACCOUNT_ID
  AND D.IS_CURRENT = TRUE
  AND F.ACCOUNT_KEY IS NULL;

------------------------------------------------------------------------------
-- BRANCH_KEY
------------------------------------------------------------------------------

UPDATE FACT_FRAUD F
SET BRANCH_KEY = D.BRANCH_KEY
FROM DIM_BRANCH D
WHERE F.BRANCH_ID = D.BRANCH_ID
  AND F.BRANCH_KEY IS NULL;

------------------------------------------------------------------------------
-- DATE_KEY
------------------------------------------------------------------------------

UPDATE FACT_FRAUD F
SET DATE_KEY = D.DATE_KEY
FROM DIM_DATE D
WHERE F.DETECTED_DATE = D.FULL_DATE
  AND F.DATE_KEY IS NULL;

------------------------------------------------------------------------------
-- MERCHANT_KEY
--
-- FACT_FRAUD does not contain TRANSACTION_CITY / TRANSACTION_STATE.
-- Leave MERCHANT_KEY NULL for now to avoid ambiguous matches.
------------------------------------------------------------------------------