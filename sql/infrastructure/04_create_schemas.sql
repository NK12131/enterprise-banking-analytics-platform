/*****************************************************************************************
 Script Name : 04_create_schemas.sql
******************************************************************************************/

USE ROLE SYSADMIN;

USE DATABASE BANKING_ANALYTICS_DB;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;
CREATE SCHEMA IF NOT EXISTS AUDIT;
CREATE SCHEMA IF NOT EXISTS CONFIG;
CREATE SCHEMA IF NOT EXISTS UTILS;