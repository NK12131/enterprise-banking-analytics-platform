/*****************************************************************************************
 Script Name : 09_create_streams.sql
******************************************************************************************/

USE DATABASE BANKING_ANALYTICS_DB;
USE SCHEMA SILVER;

CREATE STREAM IF NOT EXISTS STRM_CUSTOMERS
ON TABLE CUSTOMER;

CREATE STREAM IF NOT EXISTS STRM_TRANSACTIONS
ON TABLE TRANSACTION;