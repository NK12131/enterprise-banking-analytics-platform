/*****************************************************************************************
 Script Name : 12_create_resource_monitors.sql
******************************************************************************************/

CREATE RESOURCE MONITOR IF NOT EXISTS RM_BANKING_MONTHLY

WITH CREDIT_QUOTA=100

TRIGGERS
ON 80 PERCENT DO NOTIFY
ON 90 PERCENT DO NOTIFY
ON 100 PERCENT DO SUSPEND;