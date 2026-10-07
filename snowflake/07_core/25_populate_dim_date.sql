USE DATABASE ENTERPRISE_BANKING;
USE SCHEMA CORE;

-- Remove existing data (safe for rebuilds)
TRUNCATE TABLE DIM_DATE;

INSERT INTO DIM_DATE
(
    DATE_KEY,
    FULL_DATE,
    YEAR,
    QUARTER,
    MONTH,
    MONTH_NAME,
    MONTH_SHORT,
    WEEK_OF_YEAR,
    DAY_OF_MONTH,
    DAY_OF_WEEK,
    DAY_NAME,
    DAY_OF_YEAR,
    IS_WEEKEND,
    IS_MONTH_START,
    IS_MONTH_END,
    IS_QUARTER_START,
    IS_QUARTER_END,
    IS_YEAR_START,
    IS_YEAR_END,
    FISCAL_YEAR
)

WITH DATE_SERIES AS
(
    SELECT

        DATEADD
        (
            DAY,
            ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1,
            '2000-01-01'::DATE
        ) AS DATE_VALUE

    FROM TABLE
    (
        GENERATOR
        (
            ROWCOUNT => 18628
        )
    )
)

SELECT

    TO_NUMBER(
        TO_CHAR(DATE_VALUE,'YYYYMMDD')
    )                                                AS DATE_KEY,

    DATE_VALUE                                       AS FULL_DATE,

    YEAR(DATE_VALUE)                                 AS YEAR,

    QUARTER(DATE_VALUE)                              AS QUARTER,

    MONTH(DATE_VALUE)                                AS MONTH,

    MONTHNAME(DATE_VALUE)                            AS MONTH_NAME,

    LEFT(
        MONTHNAME(DATE_VALUE),
        3
    )                                                AS MONTH_SHORT,

    WEEKOFYEAR(DATE_VALUE)                           AS WEEK_OF_YEAR,

    DAY(DATE_VALUE)                                  AS DAY_OF_MONTH,

    DAYOFWEEKISO(DATE_VALUE)                         AS DAY_OF_WEEK,

    DAYNAME(DATE_VALUE)                              AS DAY_NAME,

    DAYOFYEAR(DATE_VALUE)                            AS DAY_OF_YEAR,

    DAYOFWEEKISO(DATE_VALUE) IN (6,7)                AS IS_WEEKEND,

    DAY(DATE_VALUE)=1                                AS IS_MONTH_START,

    LAST_DAY(DATE_VALUE)=DATE_VALUE                  AS IS_MONTH_END,

    DATE_TRUNC('QUARTER',DATE_VALUE)=DATE_VALUE      AS IS_QUARTER_START,

    LAST_DAY(
        DATE_TRUNC('QUARTER',DATE_VALUE),
        'QUARTER'
    ) = DATE_VALUE                                   AS IS_QUARTER_END,

    DATE_TRUNC('YEAR',DATE_VALUE)=DATE_VALUE         AS IS_YEAR_START,

    LAST_DAY(
        DATE_TRUNC('YEAR',DATE_VALUE),
        'YEAR'
    ) = DATE_VALUE                                   AS IS_YEAR_END,

    YEAR(DATE_VALUE)                                 AS FISCAL_YEAR

FROM DATE_SERIES

ORDER BY DATE_VALUE;
