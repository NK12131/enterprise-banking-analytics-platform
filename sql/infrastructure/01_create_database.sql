/*****************************************************************************************
 Script Name : 01_create_database.sql
 Description : Create Banking Analytics Database
 Author      : Subashini
******************************************************************************************/

USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS BANKING_ANALYTICS_DB
COMMENT='Enterprise Banking Analytics Platform';

USE DATABASE BANKING_ANALYTICS_DB;