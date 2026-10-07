USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

CREATE OR REPLACE PROCEDURE PROCESS_FACT_LOANS()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE

    V_STREAM_HAS_DATA BOOLEAN DEFAULT FALSE;

    V_INSERTED_ROWS NUMBER DEFAULT 0;

BEGIN

    --------------------------------------------------------------------------
    -- STEP 1 : Check Stream
    --------------------------------------------------------------------------

    SELECT SYSTEM$STREAM_HAS_DATA(
        'ENTERPRISE_BANKING.RAW.STR_RAW_LOANS'
    )
    INTO :V_STREAM_HAS_DATA;

    IF (NOT V_STREAM_HAS_DATA) THEN

        RETURN 'No new loan records found.';

    END IF;

    --------------------------------------------------------------------------
    -- STEP 2 : Begin Transaction
    --------------------------------------------------------------------------

    BEGIN TRANSACTION;

    --------------------------------------------------------------------------
    -- STEP 3 : Merge
    --------------------------------------------------------------------------

    MERGE INTO CORE.FACT_LOANS T

    USING
    (

        SELECT

            L.LOAN_ID,

            DC.CUSTOMER_KEY,
            L.CUSTOMER_ID,

            DA.ACCOUNT_KEY,
            L.ACCOUNT_ID,

            DB.BRANCH_KEY,
            L.BRANCH_ID,

            DD.DATE_KEY,

            L.LOAN_TYPE,

            L.LOAN_STATUS,

            L.ORIGINAL_PRINCIPAL,

            L.OUTSTANDING_BALANCE,

            L.INTEREST_RATE,

            L.TERM_MONTHS,

            L.MONTHLY_PAYMENT,

            L.CURRENCY_CODE,

            L.ORIGINATION_DATE,

            L.MATURITY_DATE,

            L.SOURCE_FILE,

            L.LOAD_TIMESTAMP
                AS RAW_LOAD_TIMESTAMP

        FROM STAGING.STG_LOANS L

        LEFT JOIN CORE.DIM_CUSTOMER DC
            ON L.CUSTOMER_ID = DC.CUSTOMER_ID
           AND DC.IS_CURRENT = TRUE

        LEFT JOIN CORE.DIM_ACCOUNT DA
            ON L.ACCOUNT_ID = DA.ACCOUNT_ID
           AND DA.IS_CURRENT = TRUE

        LEFT JOIN CORE.DIM_BRANCH DB
            ON L.BRANCH_ID = DB.BRANCH_ID

        LEFT JOIN CORE.DIM_DATE DD
            ON DD.FULL_DATE = L.ORIGINATION_DATE

    ) S

    ON T.LOAN_ID = S.LOAN_ID

    WHEN MATCHED THEN

        UPDATE SET

            CUSTOMER_KEY         = S.CUSTOMER_KEY,
            ACCOUNT_KEY          = S.ACCOUNT_KEY,
            BRANCH_KEY           = S.BRANCH_KEY,
            DATE_KEY             = S.DATE_KEY,

            LOAN_STATUS          = S.LOAN_STATUS,

            ORIGINAL_PRINCIPAL   = S.ORIGINAL_PRINCIPAL,

            OUTSTANDING_BALANCE  = S.OUTSTANDING_BALANCE,

            INTEREST_RATE        = S.INTEREST_RATE,

            TERM_MONTHS          = S.TERM_MONTHS,

            MONTHLY_PAYMENT      = S.MONTHLY_PAYMENT,

            MATURITY_DATE        = S.MATURITY_DATE,

            RAW_LOAD_TIMESTAMP   = S.RAW_LOAD_TIMESTAMP,

            SOURCE_FILE          = S.SOURCE_FILE

    WHEN NOT MATCHED THEN

        INSERT
        (
            LOAN_ID,

            CUSTOMER_KEY,
            CUSTOMER_ID,

            ACCOUNT_KEY,
            ACCOUNT_ID,

            BRANCH_KEY,
            BRANCH_ID,

            DATE_KEY,

            LOAN_TYPE,

            LOAN_STATUS,

            ORIGINAL_PRINCIPAL,

            OUTSTANDING_BALANCE,

            INTEREST_RATE,

            TERM_MONTHS,

            MONTHLY_PAYMENT,

            CURRENCY_CODE,

            ORIGINATION_DATE,

            MATURITY_DATE,

            SOURCE_FILE,

            RAW_LOAD_TIMESTAMP
        )

        VALUES
        (
            S.LOAN_ID,

            S.CUSTOMER_KEY,
            S.CUSTOMER_ID,

            S.ACCOUNT_KEY,
            S.ACCOUNT_ID,

            S.BRANCH_KEY,
            S.BRANCH_ID,

            S.DATE_KEY,

            S.LOAN_TYPE,

            S.LOAN_STATUS,

            S.ORIGINAL_PRINCIPAL,

            S.OUTSTANDING_BALANCE,

            S.INTEREST_RATE,

            S.TERM_MONTHS,

            S.MONTHLY_PAYMENT,

            S.CURRENCY_CODE,

            S.ORIGINATION_DATE,

            S.MATURITY_DATE,

            S.SOURCE_FILE,

            S.RAW_LOAD_TIMESTAMP
        );

    --------------------------------------------------------------------------
    -- STEP 4 : Metrics
    --------------------------------------------------------------------------

    V_INSERTED_ROWS := SQLROWCOUNT;

    --------------------------------------------------------------------------
    -- STEP 5 : Commit
    --------------------------------------------------------------------------

    COMMIT;

    --------------------------------------------------------------------------
    -- STEP 6 : Return
    --------------------------------------------------------------------------

    RETURN
        'FACT_LOANS Incremental Load Completed | Rows Processed = '
        || V_INSERTED_ROWS;

EXCEPTION

    WHEN OTHER THEN

        ROLLBACK;

        RAISE;

END;

$$;