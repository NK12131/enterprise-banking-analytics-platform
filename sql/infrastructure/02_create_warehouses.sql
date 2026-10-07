/*****************************************************************************************
 Script Name : 02_create_warehouses.sql
 Description : Create Virtual Warehouses
******************************************************************************************/

USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS WH_INGEST
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT='Warehouse for Snowpipe and COPY INTO operations';

CREATE WAREHOUSE IF NOT EXISTS WH_TRANSFORM
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT='Warehouse for Snowpark and dbt transformations';

CREATE WAREHOUSE IF NOT EXISTS WH_ANALYTICS
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT='Warehouse for BI reporting';

CREATE WAREHOUSE IF NOT EXISTS WH_ADMIN
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT='Warehouse for administrative activities';