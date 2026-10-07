USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

CREATE OR REPLACE PROCEDURE PROCESS_FACT_CREDIT_CARDS()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE

    V_STREAM_HAS_DATA BOOLEAN DEFAULT FALSE;

    V_ROWS_PROCESSED NUMBER DEFAULT 0;

BEGIN

    ----------------------------------------------------------------------------
    -- STEP 1 : Check Stream
    ----------------------------------------------------------------------------

    SELECT SYSTEM$STREAM_HAS_DATA(
        'ENTERPRISE_BANKING.RAW.STR_RAW_CREDIT_CARDS'
    )
    INTO :V_STREAM_HAS_DATA;

    IF (NOT V_STREAM_HAS_DATA) THEN

        RETURN 'No new credit card records found.';

    END IF;

    ----------------------------------------------------------------------------
    -- STEP 2 : Begin Transaction
    ----------------------------------------------------------------------------

    BEGIN TRANSACTION;

    ----------------------------------------------------------------------------
    -- STEP 3 : Merge Incremental Records
    ----------------------------------------------------------------------------

    MERGE INTO CORE.FACT_CREDIT_CARDS T

    USING
    (

        SELECT

            C.CARD_ID,

            DC.CUSTOMER_KEY,
            C.CUSTOMER_ID,

            DA.ACCOUNT_KEY,
            C.ACCOUNT_ID,

            DB.BRANCH_KEY,
            C.BRANCH_ID,

            DD.DATE_KEY,

            C.CARD_PRODUCT,

            C.CARD_STATUS,

            C.CREDIT_LIMIT,

            C.CURRENT_BALANCE,

            C.AVAILABLE_CREDIT,

            C.APR,

            C.ISSUED_DATE,

            C.EXPIRATION_DATE,

            C.CURRENCY_CODE,

            C.SOURCE_FILE,

            C.LOAD_TIMESTAMP
                AS RAW_LOAD_TIMESTAMP

        FROM STAGING.STG_CREDIT_CARDS C

        LEFT JOIN CORE.DIM_CUSTOMER DC
            ON C.CUSTOMER_ID = DC.CUSTOMER_ID
           AND DC.IS_CURRENT = TRUE

        LEFT JOIN CORE.DIM_ACCOUNT DA
            ON C.ACCOUNT_ID = DA.ACCOUNT_ID
           AND DA.IS_CURRENT = TRUE

        LEFT JOIN CORE.DIM_BRANCH DB
            ON C.BRANCH_ID = DB.BRANCH_ID

        LEFT JOIN CORE.DIM_DATE DD
            ON DD.FULL_DATE = C.ISSUED_DATE

    ) S

    ON T.CARD_ID = S.CARD_ID

    WHEN MATCHED THEN

        UPDATE SET

            CUSTOMER_KEY        = S.CUSTOMER_KEY,
            ACCOUNT_KEY         = S.ACCOUNT_KEY,
            BRANCH_KEY          = S.BRANCH_KEY,
            DATE_KEY            = S.DATE_KEY,

            CARD_STATUS         = S.CARD_STATUS,

            CREDIT_LIMIT        = S.CREDIT_LIMIT,

            CURRENT_BALANCE     = S.CURRENT_BALANCE,

            AVAILABLE_CREDIT    = S.AVAILABLE_CREDIT,

            APR                 = S.APR,

            EXPIRATION_DATE     = S.EXPIRATION_DATE,

            SOURCE_FILE         = S.SOURCE_FILE,

            RAW_LOAD_TIMESTAMP  = S.RAW_LOAD_TIMESTAMP

    WHEN NOT MATCHED THEN

        INSERT
        (
            CARD_ID,

            CUSTOMER_KEY,
            CUSTOMER_ID,

            ACCOUNT_KEY,
            ACCOUNT_ID,

            BRANCH_KEY,
            BRANCH_ID,

            DATE_KEY,

            CARD_PRODUCT,

            CARD_STATUS,

            CREDIT_LIMIT,

            CURRENT_BALANCE,

            AVAILABLE_CREDIT,

            APR,

            ISSUED_DATE,

            EXPIRATION_DATE,

            CURRENCY_CODE,

            SOURCE_FILE,

            RAW_LOAD_TIMESTAMP
        )

        VALUES
        (
            S.CARD_ID,

            S.CUSTOMER_KEY,
            S.CUSTOMER_ID,

            S.ACCOUNT_KEY,
            S.ACCOUNT_ID,

            S.BRANCH_KEY,
            S.BRANCH_ID,

            S.DATE_KEY,

            S.CARD_PRODUCT,

            S.CARD_STATUS,

            S.CREDIT_LIMIT,

            S.CURRENT_BALANCE,

            S.AVAILABLE_CREDIT,

            S.APR,

            S.ISSUED_DATE,

            S.EXPIRATION_DATE,

            S.CURRENCY_CODE,

            S.SOURCE_FILE,

            S.RAW_LOAD_TIMESTAMP
        );

    ----------------------------------------------------------------------------
    -- STEP 4 : Metrics
    ----------------------------------------------------------------------------

    V_ROWS_PROCESSED := SQLROWCOUNT;

    ----------------------------------------------------------------------------
    -- STEP 5 : Commit
    ----------------------------------------------------------------------------

    COMMIT;

    ----------------------------------------------------------------------------
    -- STEP 6 : Return
    ----------------------------------------------------------------------------

    RETURN
        'FACT_CREDIT_CARDS Incremental Load Completed | Rows Processed = '
        || V_ROWS_PROCESSED;

EXCEPTION

    WHEN OTHER THEN

        ROLLBACK;

        RAISE;

END;

$$;