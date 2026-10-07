/*****************************************************************************************
 Script Name : 08_create_pipes.sql
******************************************************************************************/

USE DATABASE BANKING_ANALYTICS_DB;
USE SCHEMA RAW;

CREATE PIPE IF NOT EXISTS PIPE_CUSTOMERS
AUTO_INGEST=TRUE
AS
COPY INTO BRONZE.BRONZE_CUSTOMERS
FROM @STG_BANKING_RAW/customers
FILE_FORMAT=(FORMAT_NAME=FF_JSON);

CREATE PIPE IF NOT EXISTS PIPE_TRANSACTIONS
AUTO_INGEST=TRUE
AS
COPY INTO BRONZE.BRONZE_TRANSACTIONS
FROM @STG_BANKING_RAW/transactions
FILE_FORMAT=(FORMAT_NAME=FF_PARQUET);