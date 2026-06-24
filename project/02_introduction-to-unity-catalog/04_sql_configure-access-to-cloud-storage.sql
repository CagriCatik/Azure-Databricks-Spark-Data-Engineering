-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Configure Access to Cloud Storage via Unity Catalog
-- MAGIC
-- MAGIC This notebook explains how to connect Databricks Unity Catalog to external cloud storage.
-- MAGIC
-- MAGIC In this example, the cloud storage is Azure Data Lake Storage Gen2.
-- MAGIC
-- MAGIC Example storage path:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/ -- MAGIC `
-- MAGIC
-- MAGIC Unity Catalog uses the following objects for governed cloud storage access:
-- MAGIC
-- MAGIC `text -- MAGIC Storage Credential -- MAGIC   External Location -- MAGIC     External Table -- MAGIC     External Volume -- MAGIC     File access -- MAGIC `
-- MAGIC
-- MAGIC Key idea:
-- MAGIC
-- MAGIC A storage credential stores the cloud identity.
-- MAGIC An external location maps that credential to a specific cloud storage path.
-- MAGIC Users are then granted permissions on the external location.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Check whether the workspace is attached to a Unity Catalog metastore
-- MAGIC
-- MAGIC External locations are Unity Catalog objects.
-- MAGIC
-- MAGIC If this returns a value, the workspace is attached to a Unity Catalog metastore.
-- MAGIC
-- MAGIC If this returns `NULL` or fails, Unity Catalog is probably not enabled for this workspace.

-- COMMAND ----------

SELECT current_metastore();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Check current catalog and schema
-- MAGIC
-- MAGIC This is not strictly required for creating an external location.
-- MAGIC
-- MAGIC It is useful context because external tables and volumes are created under:
-- MAGIC
-- MAGIC `text -- MAGIC catalog.schema.object -- MAGIC `

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

SELECT current_schema();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Try direct access to cloud storage
-- MAGIC
-- MAGIC This command lists the Azure Data Lake Storage path directly.
-- MAGIC
-- MAGIC In many secure Unity Catalog setups, direct access may fail unless:
-- MAGIC
-- MAGIC - the cluster has legacy storage credentials configured, or
-- MAGIC - the user has access through Unity Catalog external locations, or
-- MAGIC - the workspace is configured with the required cloud identity.
-- MAGIC
-- MAGIC Path:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/ -- MAGIC `

-- COMMAND ----------

-- MAGIC %fs ls 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/'

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Show existing storage credentials
-- MAGIC
-- MAGIC A storage credential represents a cloud identity that Unity Catalog can use to access cloud storage.
-- MAGIC
-- MAGIC For Azure, this is commonly backed by:
-- MAGIC
-- MAGIC - an Azure managed identity, or
-- MAGIC - an Azure service principal.
-- MAGIC
-- MAGIC This command may fail if you do not have permission to view storage credentials.

-- COMMAND ----------

SHOW STORAGE CREDENTIALS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Describe the storage credential
-- MAGIC
-- MAGIC This checks whether the expected storage credential exists.
-- MAGIC
-- MAGIC In this tutorial, the storage credential is:
-- MAGIC
-- MAGIC `text -- MAGIC databricks-course-sc -- MAGIC `
-- MAGIC
-- MAGIC Backticks are required because the name contains hyphens.

-- COMMAND ----------

DESCRIBE STORAGE CREDENTIAL `databricks-course-sc`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Required permission on the storage credential
-- MAGIC
-- MAGIC To create an external location using a storage credential, the user usually needs permission to create external locations on that storage credential.
-- MAGIC
-- MAGIC Example:
-- MAGIC
-- MAGIC ``sql -- MAGIC GRANT CREATE EXTERNAL LOCATION -- MAGIC ON STORAGE CREDENTIAL `databricks-course-sc` -- MAGIC TO `data-admins`; -- MAGIC ``
-- MAGIC
-- MAGIC Do not run this unless you are allowed to manage Unity Catalog permissions.

-- COMMAND ----------

-- GRANT CREATE EXTERNAL LOCATION
-- ON STORAGE CREDENTIAL `databricks-course-sc`
-- TO `data-admins`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Create an external location
-- MAGIC
-- MAGIC An external location maps a cloud storage path to a Unity Catalog storage credential.
-- MAGIC
-- MAGIC External location name:
-- MAGIC
-- MAGIC `text -- MAGIC databricks_course_ext_dl1_demo -- MAGIC `
-- MAGIC
-- MAGIC Storage path:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/ -- MAGIC `
-- MAGIC
-- MAGIC Storage credential:
-- MAGIC
-- MAGIC `text -- MAGIC databricks-course-sc -- MAGIC `

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS databricks_course_ext_dl1_demo
URL 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL `databricks-course-sc`)
COMMENT 'External location for the demo container';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Show external locations
-- MAGIC
-- MAGIC This lists external locations visible to you.

-- COMMAND ----------

SHOW EXTERNAL LOCATIONS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Describe the external location
-- MAGIC
-- MAGIC This shows metadata such as:
-- MAGIC
-- MAGIC - URL
-- MAGIC - credential name
-- MAGIC - owner
-- MAGIC - comment
-- MAGIC - access information

-- COMMAND ----------

DESCRIBE EXTERNAL LOCATION databricks_course_ext_dl1_demo;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Show grants on the external location
-- MAGIC
-- MAGIC This may fail if you do not have permission to inspect grants.

-- COMMAND ----------

SHOW GRANTS ON EXTERNAL LOCATION databricks_course_ext_dl1_demo;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 11. Grant access to the external location
-- MAGIC
-- MAGIC Common external location privileges:
-- MAGIC
-- MAGIC `text -- MAGIC READ FILES -- MAGIC WRITE FILES -- MAGIC CREATE EXTERNAL TABLE -- MAGIC CREATE EXTERNAL VOLUME -- MAGIC `
-- MAGIC
-- MAGIC Typical read-only file access:
-- MAGIC
-- MAGIC `text -- MAGIC READ FILES -- MAGIC `
-- MAGIC
-- MAGIC Typical external table creation access:
-- MAGIC
-- MAGIC `text -- MAGIC READ FILES -- MAGIC WRITE FILES -- MAGIC CREATE EXTERNAL TABLE -- MAGIC `
-- MAGIC
-- MAGIC Replace `data-users` with a real Databricks group.
-- MAGIC
-- MAGIC Do not run these unless you are allowed to manage access.

-- COMMAND ----------

-- GRANT READ FILES
-- ON EXTERNAL LOCATION databricks_course_ext_dl1_demo
-- TO `data-users`;

-- COMMAND ----------

-- GRANT READ FILES, WRITE FILES
-- ON EXTERNAL LOCATION databricks_course_ext_dl1_demo
-- TO `data-engineers`;

-- COMMAND ----------

-- GRANT READ FILES, WRITE FILES, CREATE EXTERNAL TABLE
-- ON EXTERNAL LOCATION databricks_course_ext_dl1_demo
-- TO `data-engineers`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 12. List files through the external location path
-- MAGIC
-- MAGIC After the external location exists and the user has `READ FILES`, file listing should be governed by Unity Catalog.
-- MAGIC
-- MAGIC This still uses the cloud URI, but access is controlled by Unity Catalog.

-- COMMAND ----------

LIST 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 13. Create a catalog and schema for external table examples
-- MAGIC
-- MAGIC External tables still live inside a catalog and schema.
-- MAGIC
-- MAGIC This section creates a small practice namespace.
-- MAGIC
-- MAGIC If you already have a catalog and schema, replace these names.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS dev_catalog
COMMENT 'Development catalog for Unity Catalog external storage learning';

-- COMMAND ----------

USE CATALOG dev_catalog;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS external_storage
COMMENT 'Schema for external storage examples';

-- COMMAND ----------

USE SCHEMA external_storage;

-- COMMAND ----------

SELECT current_catalog(), current_schema();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 14. Create an external table
-- MAGIC
-- MAGIC An external table stores metadata in Unity Catalog, but the data files remain in the external cloud storage path.
-- MAGIC
-- MAGIC Important:
-- MAGIC
-- MAGIC - The `LOCATION` path must be under a valid external location.
-- MAGIC - The user needs `CREATE EXTERNAL TABLE` on the external location.
-- MAGIC - The user also needs table-creation privileges in the target schema.
-- MAGIC
-- MAGIC The following example assumes there is a Delta table folder under:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta -- MAGIC `
-- MAGIC
-- MAGIC Do not run unless that folder exists and contains a valid Delta table.

-- COMMAND ----------

-- CREATE TABLE IF NOT EXISTS customers_external
-- LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 15. Create an external table from query output
-- MAGIC
-- MAGIC This creates a new external Delta table at a location under the external location.
-- MAGIC
-- MAGIC Use this only if:
-- MAGIC
-- MAGIC - you have `WRITE FILES`
-- MAGIC - you have `CREATE EXTERNAL TABLE`
-- MAGIC - the target path is empty or safe to use
-- MAGIC
-- MAGIC Example output path:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/generated_customers -- MAGIC `

-- COMMAND ----------

-- CREATE OR REPLACE TABLE generated_customers_external
-- LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/generated_customers'
-- AS
-- SELECT
--   1 AS customer_id,
--   'Ada Lovelace' AS customer_name,
--   'UK' AS country
-- UNION ALL
-- SELECT
--   2 AS customer_id,
--   'Alan Turing' AS customer_name,
--   'UK' AS country;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 16. Query the external table
-- MAGIC
-- MAGIC Uncomment this after creating the external table.

-- COMMAND ----------

-- SELECT *
-- FROM generated_customers_external;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 17. Create an external volume
-- MAGIC
-- MAGIC External volumes are Unity Catalog objects for governing non-tabular files in cloud storage.
-- MAGIC
-- MAGIC Use external volumes for:
-- MAGIC
-- MAGIC - raw files
-- MAGIC - CSV files
-- MAGIC - JSON files
-- MAGIC - images
-- MAGIC - model artifacts
-- MAGIC - configuration files
-- MAGIC
-- MAGIC The external volume path must be under the external location.
-- MAGIC
-- MAGIC Example volume path:
-- MAGIC
-- MAGIC `text -- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/volumes/demo_files -- MAGIC `

-- COMMAND ----------

-- CREATE EXTERNAL VOLUME IF NOT EXISTS demo_files_volume
-- LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/volumes/demo_files'
-- COMMENT 'External volume for demo files';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 18. List files in an external volume
-- MAGIC
-- MAGIC Unity Catalog volume paths use this format:
-- MAGIC
-- MAGIC `text -- MAGIC /Volumes/catalog/schema/volume/ -- MAGIC `
-- MAGIC
-- MAGIC Uncomment after creating the external volume.

-- COMMAND ----------

-- LIST '/Volumes/dev_catalog/external_storage/demo_files_volume/';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 19. Read files directly from the external location
-- MAGIC
-- MAGIC If files exist and you have permission, you can query them directly by path.
-- MAGIC
-- MAGIC Example for CSV files.
-- MAGIC
-- MAGIC Uncomment and adjust the path if a CSV file exists.

-- COMMAND ----------

-- SELECT *
-- FROM csv.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/files/customers.csv`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Example for Parquet files.
-- MAGIC
-- MAGIC Uncomment and adjust the path if Parquet files exist.

-- COMMAND ----------

-- SELECT *
-- FROM parquet.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/files/customers_parquet/`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Example for Delta files.
-- MAGIC
-- MAGIC Uncomment and adjust the path if a Delta table exists at the path.

-- COMMAND ----------

-- SELECT *
-- FROM delta.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta/`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 20. Common errors
-- MAGIC
-- MAGIC ### Error: `No parent external location found`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - the path is not covered by any external location
-- MAGIC - the external location URL is wrong
-- MAGIC - the table or volume location is outside the registered external location
-- MAGIC
-- MAGIC ### Error: `Permission denied`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - missing `READ FILES`
-- MAGIC - missing `WRITE FILES`
-- MAGIC - missing `CREATE EXTERNAL TABLE`
-- MAGIC - missing `CREATE EXTERNAL VOLUME`
-- MAGIC - missing schema-level privileges
-- MAGIC
-- MAGIC ### Error: `Storage credential does not exist`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - wrong credential name
-- MAGIC - missing permission to see the credential
-- MAGIC - credential was created in another metastore
-- MAGIC
-- MAGIC ### Error: `AbfsRestOperationException`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - Azure identity does not have access to the storage account
-- MAGIC - missing Azure RBAC role
-- MAGIC - storage account firewall or networking issue
-- MAGIC - wrong container or storage account name
-- MAGIC
-- MAGIC ### Error: `Path does not exist`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - folder does not exist
-- MAGIC - wrong path
-- MAGIC - no files have been written yet
-- MAGIC - user has permission to the external location but the cloud path is empty

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 21. Cleanup
-- MAGIC
-- MAGIC Run only if you want to delete the practice objects.
-- MAGIC
-- MAGIC Be careful:
-- MAGIC
-- MAGIC - Dropping an external table removes table metadata.
-- MAGIC - It does not normally delete the underlying external data files.
-- MAGIC - Dropping an external location removes the Unity Catalog object, not the cloud storage container.
-- MAGIC - Dropping a storage credential can break all external locations that use it.

-- COMMAND ----------

-- DROP TABLE IF EXISTS generated_customers_external;

-- COMMAND ----------

-- DROP VOLUME IF EXISTS demo_files_volume;

-- COMMAND ----------

-- DROP SCHEMA IF EXISTS dev_catalog.external_storage CASCADE;

-- COMMAND ----------

-- DROP CATALOG IF EXISTS dev_catalog CASCADE;

-- COMMAND ----------

-- DROP EXTERNAL LOCATION IF EXISTS databricks_course_ext_dl1_demo;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary
-- MAGIC
-- MAGIC You learned:
-- MAGIC
-- MAGIC - how Unity Catalog governs external cloud storage
-- MAGIC - what a storage credential is
-- MAGIC - what an external location is
-- MAGIC - how to create an external location for Azure ADLS Gen2
-- MAGIC - how to inspect external locations
-- MAGIC - how to grant file and table privileges
-- MAGIC - how to create external table examples
-- MAGIC - how to create external volume examples
-- MAGIC - how to troubleshoot common permission and path errors
-- MAGIC
-- MAGIC Core model:
-- MAGIC
-- MAGIC `text -- MAGIC Cloud identity -- MAGIC   -> Storage Credential -- MAGIC      -> External Location -- MAGIC         -> READ FILES / WRITE FILES / CREATE EXTERNAL TABLE / CREATE EXTERNAL VOLUME -- MAGIC         -> External Tables -- MAGIC         -> External Volumes -- MAGIC `
