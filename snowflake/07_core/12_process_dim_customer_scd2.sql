USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;


CREATE OR REPLACE PROCEDURE PROCESS_DIM_CUSTOMER_SCD2()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$

DECLARE

    V_CHANGE_COUNT NUMBER DEFAULT 0;
    V_EXPIRED_COUNT NUMBER DEFAULT 0;
    V_INSERTED_COUNT NUMBER DEFAULT 0;

    SCD2_VALIDATION_ERROR EXCEPTION
    (
        -20001,
        'SCD2 validation failed: multiple current customer versions detected'
    );

BEGIN

    BEGIN TRANSACTION;


    /* ================================================================
       STEP 1: Materialize customer stream changes
       ================================================================ */

    CREATE OR REPLACE TEMPORARY TABLE TMP_CUSTOMER_CHANGES AS

    SELECT

        RAW_RECORD:customer_id::VARCHAR
            AS CUSTOMER_ID,

        RAW_RECORD:branch_id::VARCHAR
            AS BRANCH_ID,

        RAW_RECORD:first_name::VARCHAR
            AS FIRST_NAME,

        RAW_RECORD:last_name::VARCHAR
            AS LAST_NAME,

        TRY_TO_DATE(
            RAW_RECORD:date_of_birth::VARCHAR
        ) AS DATE_OF_BIRTH,

        RAW_RECORD:gender::VARCHAR
            AS GENDER,

        RAW_RECORD:email::VARCHAR
            AS EMAIL,

        RAW_RECORD:phone_number::VARCHAR
            AS PHONE_NUMBER,

        RAW_RECORD:city::VARCHAR
            AS CITY,

        RAW_RECORD:state::VARCHAR
            AS STATE,

        RAW_RECORD:zip_code::VARCHAR
            AS ZIP_CODE,

        RAW_RECORD:customer_profile::VARCHAR
            AS CUSTOMER_PROFILE,

        RAW_RECORD:customer_status::VARCHAR
            AS CUSTOMER_STATUS,

        TRY_TO_DECIMAL(
            RAW_RECORD:annual_income::VARCHAR,
            18,
            2
        ) AS ANNUAL_INCOME,

        TRY_TO_NUMBER(
            RAW_RECORD:credit_score::VARCHAR
        ) AS CREDIT_SCORE,

        TRY_TO_DATE(
            RAW_RECORD:customer_since::VARCHAR
        ) AS CUSTOMER_SINCE,

        SHA2(
            CONCAT_WS(
                '|',

                COALESCE(
                    RAW_RECORD:branch_id::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:email::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:phone_number::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:city::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:state::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:zip_code::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:customer_profile::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:customer_status::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:annual_income::VARCHAR,
                    ''
                ),

                COALESCE(
                    RAW_RECORD:credit_score::VARCHAR,
                    ''
                )
            ),
            256
        ) AS RECORD_HASH,

        SOURCE_FILE,

        SOURCE_ROW_NUMBER,

        LOAD_TIMESTAMP
            AS RAW_LOAD_TIMESTAMP

    FROM RAW.STR_RAW_CUSTOMERS

    WHERE METADATA$ACTION = 'INSERT'

    QUALIFY ROW_NUMBER() OVER
    (
        PARTITION BY
            RAW_RECORD:customer_id::VARCHAR

        ORDER BY
            LOAD_TIMESTAMP DESC,
            SOURCE_ROW_NUMBER DESC
    ) = 1;


    SELECT COUNT(*)
    INTO :V_CHANGE_COUNT
    FROM TMP_CUSTOMER_CHANGES;


    /* ================================================================
       STEP 2: Classify SCD actions
       ================================================================ */

    CREATE OR REPLACE TEMPORARY TABLE TMP_CUSTOMER_SCD_ACTIONS AS

    SELECT

        SOURCE.*,

        CASE

            WHEN TARGET.CUSTOMER_ID IS NULL
                THEN 'NEW'

            WHEN TARGET.RECORD_HASH
                IS DISTINCT FROM SOURCE.RECORD_HASH
                THEN 'CHANGED'

            ELSE 'UNCHANGED'

        END AS SCD_ACTION

    FROM TMP_CUSTOMER_CHANGES AS SOURCE

    LEFT JOIN DIM_CUSTOMER AS TARGET

        ON SOURCE.CUSTOMER_ID =
            TARGET.CUSTOMER_ID

        AND TARGET.IS_CURRENT = TRUE;


    /* ================================================================
       STEP 3: Expire changed rows
       ================================================================ */

    UPDATE DIM_CUSTOMER AS TARGET

    SET

        EFFECTIVE_TO =
            SOURCE.RAW_LOAD_TIMESTAMP,

        IS_CURRENT = FALSE,

        UPDATED_TIMESTAMP =
            CURRENT_TIMESTAMP()

    FROM TMP_CUSTOMER_SCD_ACTIONS AS SOURCE

    WHERE

        TARGET.CUSTOMER_ID =
            SOURCE.CUSTOMER_ID

        AND TARGET.IS_CURRENT = TRUE

        AND SOURCE.SCD_ACTION = 'CHANGED';


    V_EXPIRED_COUNT := SQLROWCOUNT;


    /* ================================================================
       STEP 4: Insert NEW and CHANGED versions
       ================================================================ */

    INSERT INTO DIM_CUSTOMER
    (
        CUSTOMER_ID,
        BRANCH_ID,
        FIRST_NAME,
        LAST_NAME,
        DATE_OF_BIRTH,
        GENDER,
        EMAIL,
        PHONE_NUMBER,
        CITY,
        STATE,
        ZIP_CODE,
        CUSTOMER_PROFILE,
        CUSTOMER_STATUS,
        ANNUAL_INCOME,
        CREDIT_SCORE,
        CUSTOMER_SINCE,
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

        CUSTOMER_ID,
        BRANCH_ID,
        FIRST_NAME,
        LAST_NAME,
        DATE_OF_BIRTH,
        GENDER,
        EMAIL,
        PHONE_NUMBER,
        CITY,
        STATE,
        ZIP_CODE,
        CUSTOMER_PROFILE,
        CUSTOMER_STATUS,
        ANNUAL_INCOME,
        CREDIT_SCORE,
        CUSTOMER_SINCE,

        RAW_LOAD_TIMESTAMP,

        NULL,

        TRUE,

        RECORD_HASH,

        SOURCE_FILE,

        RAW_LOAD_TIMESTAMP,

        CURRENT_TIMESTAMP(),

        CURRENT_TIMESTAMP()

    FROM TMP_CUSTOMER_SCD_ACTIONS

    WHERE SCD_ACTION IN
    (
        'NEW',
        'CHANGED'
    );


    V_INSERTED_COUNT := SQLROWCOUNT;


    /* ================================================================
       STEP 5: Validate current versions
       ================================================================ */

    IF
    (
        EXISTS
        (
            SELECT 1

            FROM DIM_CUSTOMER

            WHERE IS_CURRENT = TRUE

            GROUP BY CUSTOMER_ID

            HAVING COUNT(*) > 1
        )
    )
    THEN

        RAISE SCD2_VALIDATION_ERROR;

    END IF;


    COMMIT;


    RETURN
        'DIM_CUSTOMER SCD2 completed'
        || ' | stream_rows='
        || V_CHANGE_COUNT
        || ' | expired='
        || V_EXPIRED_COUNT
        || ' | inserted='
        || V_INSERTED_COUNT;


EXCEPTION

    WHEN OTHER THEN

        ROLLBACK;

        RAISE;

END;

$$;