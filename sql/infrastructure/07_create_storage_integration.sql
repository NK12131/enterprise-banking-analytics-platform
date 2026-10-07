/*****************************************************************************************
 Script Name : 07_create_storage_integration.sql
******************************************************************************************/

-- AWS Storage Integration

CREATE STORAGE INTEGRATION IF NOT EXISTS BANKING_S3_INT
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = S3
ENABLED = TRUE
STORAGE_AWS_ROLE_ARN = '<AWS_ROLE_ARN>'
STORAGE_ALLOWED_LOCATIONS = ('s3://enterprise-banking-data/');