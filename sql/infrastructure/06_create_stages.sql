/*****************************************************************************************
 Script Name : 06_create_stages.sql
******************************************************************************************/

USE ROLE SYSADMIN;

USE DATABASE BANKING_ANALYTICS_DB;
USE SCHEMA RAW;

CREATE STAGE IF NOT EXISTS STG_BANKING_RAW
COMMENT='Landing stage for Banking source files';