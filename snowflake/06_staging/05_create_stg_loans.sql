USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA STAGING;

CREATE OR REPLACE VIEW STG_LOANS AS

SELECT
    RAW_RECORD:loan_id::VARCHAR
        AS LOAN_ID,

    RAW_RECORD:customer_id::VARCHAR
        AS CUSTOMER_ID,

    RAW_RECORD:account_id::VARCHAR
        AS ACCOUNT_ID,

    RAW_RECORD:branch_id::VARCHAR
        AS BRANCH_ID,

    RAW_RECORD:loan_type::VARCHAR
        AS LOAN_TYPE,

    RAW_RECORD:loan_status::VARCHAR
        AS LOAN_STATUS,

    RAW_RECORD:original_principal::NUMBER(18, 2)
        AS ORIGINAL_PRINCIPAL,

    RAW_RECORD:outstanding_balance::NUMBER(18, 2)
        AS OUTSTANDING_BALANCE,

    RAW_RECORD:interest_rate::NUMBER(10, 6)
        AS INTEREST_RATE,

    RAW_RECORD:term_months::NUMBER
        AS TERM_MONTHS,

    RAW_RECORD:monthly_payment::NUMBER(18, 2)
        AS MONTHLY_PAYMENT,

    RAW_RECORD:origination_date::DATE
        AS ORIGINATION_DATE,

    RAW_RECORD:maturity_date::DATE
        AS MATURITY_DATE,

    RAW_RECORD:currency_code::VARCHAR
        AS CURRENCY_CODE,

    SOURCE_FILE,

    SOURCE_ROW_NUMBER,

    LOAD_TIMESTAMP

FROM RAW.RAW_LOANS;