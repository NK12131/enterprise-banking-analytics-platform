USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

SELECT

    COUNT(*)                                      AS TOTAL_ROWS,

    COUNT(DISTINCT ACCOUNT_ID)                    AS DISTINCT_ACCOUNTS,

    COUNT_IF(IS_CURRENT)                          AS CURRENT_ROWS,

    COUNT_IF(ACCOUNT_ID IS NULL)                  AS NULL_ACCOUNT_IDS,

    COUNT_IF(
        IS_CURRENT
        AND EFFECTIVE_TO IS NOT NULL
    )                                             AS INVALID_CURRENT_ROWS,

    COUNT_IF(
        NOT IS_CURRENT
        AND EFFECTIVE_TO IS NULL
    )                                             AS INVALID_HISTORY_ROWS

FROM DIM_ACCOUNT;