USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

CREATE OR REPLACE PROCEDURE PROCESS_DIM_ACCOUNT_SCD2()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$

DECLARE

    V_STREAM_ROWS NUMBER DEFAULT 0;
    V_EXPIRED_ROWS NUMBER DEFAULT 0;
    V_INSERTED_ROWS NUMBER DEFAULT 0;
    V_DUPLICATE_CURRENT NUMBER DEFAULT 0;

    SCD2_VALIDATION_ERROR EXCEPTION
    (
        -20002,
        'Multiple current versions found for ACCOUNT_ID'
    );

BEGIN

    BEGIN TRANSACTION;

    ----------------------------------------------------------------------------
    -- STEP 1
    -- Materialize latest account changes from stream
    ----------------------------------------------------------------------------

    CREATE OR REPLACE TEMPORARY TABLE TMP_ACCOUNT_CHANGES
    AS

    SELECT

        RAW_RECORD:account_id::VARCHAR
            AS ACCOUNT_ID,

        RAW_RECORD:account_number::VARCHAR
            AS ACCOUNT_NUMBER,

        RAW_RECORD:customer_id::VARCHAR
            AS CUSTOMER_ID,

        RAW_RECORD:branch_id::VARCHAR
            AS BRANCH_ID,

        RAW_RECORD:branch_code::VARCHAR
            AS BRANCH_CODE,

        RAW_RECORD:account_type::VARCHAR
            AS ACCOUNT_TYPE,

        RAW_RECORD:account_status::VARCHAR
            AS ACCOUNT_STATUS,

        RAW_RECORD:currency_code::VARCHAR
            AS CURRENCY_CODE,

        TRY_TO_DECIMAL(
            RAW_RECORD:current_balance::VARCHAR,
            18,
            2
        ) AS CURRENT_BALANCE,

        TRY_TO_DECIMAL(
            RAW_RECORD:available_balance::VARCHAR,
            18,
            2
        ) AS AVAILABLE_BALANCE,

        TRY_TO_DECIMAL(
            RAW_RECORD:interest_rate::VARCHAR,
            10,
            6
        ) AS INTEREST_RATE,

        TRY_TO_DATE(
            RAW_RECORD:opened_date::VARCHAR
        ) AS OPENED_DATE,

        TRY_TO_DATE(
            RAW_RECORD:closed_date::VARCHAR
        ) AS CLOSED_DATE,

        SOURCE_FILE,

        SOURCE_ROW_NUMBER,

        LOAD_TIMESTAMP
            AS RAW_LOAD_TIMESTAMP,

        SHA2(

            CONCAT_WS(

                '|',

                COALESCE(
                    RAW_RECORD:customer_id::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:branch_id::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:branch_code::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:account_type::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:account_status::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:currency_code::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:interest_rate::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:closed_date::VARCHAR,
                    ''
                )

            ),

            256

        ) AS RECORD_HASH

    FROM RAW.STR_RAW_ACCOUNTS

    WHERE METADATA$ACTION = 'INSERT'

    QUALIFY ROW_NUMBER() OVER
    (
        PARTITION BY
            RAW_RECORD:account_id::VARCHAR

        ORDER BY
            LOAD_TIMESTAMP DESC,
            SOURCE_ROW_NUMBER DESC
    ) = 1;

    SELECT COUNT(*)
    INTO :V_STREAM_ROWS
    FROM TMP_ACCOUNT_CHANGES;

        ----------------------------------------------------------------------------
    -- STEP 2
    -- Classify each account as NEW / CHANGED / UNCHANGED
    ----------------------------------------------------------------------------

    CREATE OR REPLACE TEMPORARY TABLE TMP_ACCOUNT_ACTIONS
    AS

    SELECT

        SRC.*,

        CASE

            WHEN TGT.ACCOUNT_ID IS NULL
                THEN 'NEW'

            WHEN TGT.RECORD_HASH IS DISTINCT FROM SRC.RECORD_HASH
                THEN 'CHANGED'

            ELSE 'UNCHANGED'

        END AS ACTION_TYPE

    FROM TMP_ACCOUNT_CHANGES SRC

    LEFT JOIN DIM_ACCOUNT TGT

        ON SRC.ACCOUNT_ID = TGT.ACCOUNT_ID

       AND TGT.IS_CURRENT = TRUE;


    ----------------------------------------------------------------------------
    -- STEP 3
    -- Expire current versions for changed accounts
    ----------------------------------------------------------------------------

    UPDATE DIM_ACCOUNT AS TGT

    SET

        EFFECTIVE_TO =
            SRC.RAW_LOAD_TIMESTAMP,

        IS_CURRENT =
            FALSE,

        UPDATED_TIMESTAMP =
            CURRENT_TIMESTAMP()

    FROM TMP_ACCOUNT_ACTIONS SRC

    WHERE

        SRC.ACTION_TYPE = 'CHANGED'

        AND TGT.ACCOUNT_ID = SRC.ACCOUNT_ID

        AND TGT.IS_CURRENT = TRUE;


    V_EXPIRED_ROWS := SQLROWCOUNT;


    ----------------------------------------------------------------------------
    -- STEP 4
    -- Insert NEW and CHANGED versions
    ----------------------------------------------------------------------------

    INSERT INTO DIM_ACCOUNT
    (

        ACCOUNT_ID,
        ACCOUNT_NUMBER,

        CUSTOMER_ID,

        BRANCH_ID,
        BRANCH_CODE,

        ACCOUNT_TYPE,
        ACCOUNT_STATUS,

        CURRENCY_CODE,

        CURRENT_BALANCE,
        AVAILABLE_BALANCE,

        INTEREST_RATE,

        OPENED_DATE,
        CLOSED_DATE,

        EFFECTIVE_FROM,
        EFFECTIVE_TO,

        IS_CURRENT,

        RECORD_HASH,

        SOURCE_FILE,
        RAW_LOAD_TIMESTAMP,

        CREATED_TIMESTAMP,
        UPDATED_TIMESTAMP

    )

    SELECT

        ACCOUNT_ID,
        ACCOUNT_NUMBER,

        CUSTOMER_ID,

        BRANCH_ID,
        BRANCH_CODE,

        ACCOUNT_TYPE,
        ACCOUNT_STATUS,

        CURRENCY_CODE,

        CURRENT_BALANCE,
        AVAILABLE_BALANCE,

        INTEREST_RATE,

        OPENED_DATE,
        CLOSED_DATE,

        RAW_LOAD_TIMESTAMP,

        NULL,

        TRUE,

        RECORD_HASH,

        SOURCE_FILE,

        RAW_LOAD_TIMESTAMP,

        CURRENT_TIMESTAMP(),

        CURRENT_TIMESTAMP()

    FROM TMP_ACCOUNT_ACTIONS

    WHERE ACTION_TYPE IN
    (
        'NEW',
        'CHANGED'
    );


    V_INSERTED_ROWS := SQLROWCOUNT;

        ----------------------------------------------------------------------------
    -- STEP 5
    -- Validate only one current version exists per ACCOUNT_ID
    ----------------------------------------------------------------------------

    SELECT COUNT(*)
    INTO :V_DUPLICATE_CURRENT

    FROM
    (
        SELECT
            ACCOUNT_ID
        FROM DIM_ACCOUNT
        WHERE IS_CURRENT = TRUE
        GROUP BY ACCOUNT_ID
        HAVING COUNT(*) > 1
    );

    IF (V_DUPLICATE_CURRENT > 0) THEN

        RAISE SCD2_VALIDATION_ERROR;

    END IF;


    ----------------------------------------------------------------------------
    -- STEP 6
    -- Commit transaction
    ----------------------------------------------------------------------------

    COMMIT;


    ----------------------------------------------------------------------------
    -- STEP 7
    -- Return execution summary
    ----------------------------------------------------------------------------

    RETURN

        'DIM_ACCOUNT SCD2 completed'

        || ' | Stream Rows='
        || V_STREAM_ROWS

        || ' | Expired='
        || V_EXPIRED_ROWS

        || ' | Inserted='
        || V_INSERTED_ROWS;


EXCEPTION

    WHEN SCD2_VALIDATION_ERROR THEN

        ROLLBACK;

        RAISE;


    WHEN OTHER THEN

        ROLLBACK;

        RAISE;

END;

$$;