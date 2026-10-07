/*****************************************************************************************
 Script Name : 10_create_tasks.sql
******************************************************************************************/

USE DATABASE BANKING_ANALYTICS_DB;

CREATE TASK IF NOT EXISTS TASK_PROCESS_CUSTOMERS
WAREHOUSE=WH_TRANSFORM
SCHEDULE='USING CRON 0 * * * * UTC'
AS
CALL UTILS.SP_PROCESS_CUSTOMERS();

ALTER TASK TASK_PROCESS_CUSTOMERS SUSPEND;