-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Configure Access to Cloud Storage via Unity Catalog
-- MAGIC
-- MAGIC This notebook explains how to connect Databricks Unity Catalog to external
-- MAGIC cloud storage - specifically **Azure Data Lake Storage Gen2 (ADLS Gen2)**.
-- MAGIC For the rest of the Unity Catalog object model (catalogs, schemas, managed
-- MAGIC tables/volumes) see `01_uc_introduction.py`; this notebook is scoped to
-- MAGIC everything needed to govern data that lives **outside** Unity Catalog's own
-- MAGIC managed storage.
-- MAGIC
-- MAGIC Example storage path:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/
-- MAGIC ```
-- MAGIC
-- MAGIC Unity Catalog uses the following objects for governed cloud storage access:
-- MAGIC
-- MAGIC ```text
-- MAGIC Storage Credential   (cloud identity - Section 6/8 below)
-- MAGIC   External Location  (credential + path - Section 10 below)
-- MAGIC     External Table
-- MAGIC     External Volume
-- MAGIC     File access (READ FILES / WRITE FILES)
-- MAGIC ```
-- MAGIC
-- MAGIC Key idea, expanded in Section 8: a storage credential stores the cloud
-- MAGIC identity and who may use it to mint external locations; an external
-- MAGIC location then maps that credential to one specific cloud storage path, and
-- MAGIC a *separate* set of grants on the external location controls who may
-- MAGIC actually read/write files or create tables/volumes under that path. Those
-- MAGIC are two different permission layers - conflating them is the single most
-- MAGIC common source of confusing `PERMISSION_DENIED` errors in this area.

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
-- MAGIC ```text
-- MAGIC catalog.schema.object
-- MAGIC ```

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

SELECT current_schema();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. ADLS Gen2 and the hierarchical namespace
-- MAGIC
-- MAGIC Azure Data Lake Storage Gen2 is not a separate service from Azure Blob
-- MAGIC Storage - it is a Blob Storage account with the **hierarchical namespace
-- MAGIC (HNS)** feature turned on. HNS organizes objects into a real directory
-- MAGIC hierarchy (rather than Blob Storage's flat key space with `/`-delimited
-- MAGIC names that only *look* like folders), which is what makes directory rename
-- MAGIC and delete atomic metadata operations, and what allows POSIX-like
-- MAGIC file/folder ACLs.
-- MAGIC
-- MAGIC This matters here because the `abfss://` scheme (**A**zure **B**lob **F**ile
-- MAGIC **S**ystem **S**ecure) that every path in this notebook uses only works
-- MAGIC against HNS-enabled storage accounts. A storage account created without HNS
-- MAGIC is plain Blob Storage and is addressed with `wasbs://` instead - Unity
-- MAGIC Catalog external locations on Azure are built and documented around
-- MAGIC `abfss://`/ADLS Gen2, so confirm HNS is enabled on the storage account
-- MAGIC before troubleshooting anything else.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Try direct access to cloud storage
-- MAGIC
-- MAGIC This command lists the Azure Data Lake Storage path directly, bypassing
-- MAGIC Unity Catalog governance.
-- MAGIC
-- MAGIC In a properly locked-down Unity Catalog workspace this should **fail**
-- MAGIC unless:
-- MAGIC
-- MAGIC - the cluster has legacy storage credentials configured directly on it
-- MAGIC   (an anti-pattern once Unity Catalog is in use), or
-- MAGIC - access instead goes through a Unity Catalog external location
-- MAGIC   (Sections 8-11), or
-- MAGIC - the workspace has some other broader cloud identity configured.
-- MAGIC
-- MAGIC Path:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %fs ls 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/'

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Show existing storage credentials
-- MAGIC
-- MAGIC A storage credential represents a cloud identity that Unity Catalog can use
-- MAGIC to access cloud storage on your behalf.
-- MAGIC
-- MAGIC This command may fail if you do not have permission to view storage credentials.

-- COMMAND ----------

SHOW STORAGE CREDENTIALS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. What backs a storage credential on Azure
-- MAGIC
-- MAGIC On Azure, a Unity Catalog storage credential is almost always one of:
-- MAGIC
-- MAGIC - **An Azure managed identity**, via the **Access Connector for Azure
-- MAGIC   Databricks** - a small, dedicated Azure resource
-- MAGIC   (`Microsoft.Databricks/accessConnectors`) whose only job is to carry a
-- MAGIC   system-assigned managed identity. You grant that managed identity an
-- MAGIC   Azure RBAC role on the storage account - typically **Storage Blob Data
-- MAGIC   Contributor**, or a narrower reader-only role for read-only use cases -
-- MAGIC   and then reference the access connector's Azure resource ID when
-- MAGIC   creating the storage credential in Unity Catalog. This is the
-- MAGIC   Databricks-recommended approach: no secret to rotate, and the identity's
-- MAGIC   blast radius is exactly the storage account(s) it was granted a role on.
-- MAGIC - **An Azure service principal**, authenticated with a client secret or
-- MAGIC   certificate. Requires you to manage secret rotation yourself, so it is
-- MAGIC   generally a fallback for scenarios the managed-identity approach does not
-- MAGIC   cover.
-- MAGIC
-- MAGIC Either way, the Azure-side identity setup (creating the access connector,
-- MAGIC assigning the RBAC role) happens in the Azure Portal/ARM/Terraform, outside
-- MAGIC Databricks; only the resulting storage credential object is visible here.
-- MAGIC
-- MAGIC In this tutorial, the storage credential is assumed to already exist as:
-- MAGIC
-- MAGIC ```text
-- MAGIC databricks-course-sc
-- MAGIC ```
-- MAGIC
-- MAGIC Backticks are required in SQL below because the name contains hyphens.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Describe the storage credential
-- MAGIC
-- MAGIC This checks whether the expected storage credential exists, and shows
-- MAGIC which Azure identity (managed identity or service principal) backs it.

-- COMMAND ----------

DESCRIBE STORAGE CREDENTIAL `databricks-course-sc`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Two permission layers: storage credential vs. external location
-- MAGIC
-- MAGIC This is the single most important distinction in this notebook, so it gets
-- MAGIC its own section before any grants are shown.
-- MAGIC
-- MAGIC **Layer 1 - on the storage credential.** `CREATE EXTERNAL LOCATION` granted
-- MAGIC `ON STORAGE CREDENTIAL <name>` controls *who may mint new external
-- MAGIC locations* using that credential's cloud identity. This is normally
-- MAGIC restricted to a small platform/admin group - anyone with it can point a new
-- MAGIC external location at any path the underlying identity can reach.
-- MAGIC
-- MAGIC **Layer 2 - on the external location.** Once an external location exists,
-- MAGIC `READ FILES`, `WRITE FILES`, `CREATE EXTERNAL TABLE`, and
-- MAGIC `CREATE EXTERNAL VOLUME` granted `ON EXTERNAL LOCATION <name>` control what
-- MAGIC *everyday users* may do with the path it already covers.
-- MAGIC
-- MAGIC ```text
-- MAGIC Storage Credential
-- MAGIC   CREATE EXTERNAL LOCATION -> who can create new external locations here
-- MAGIC
-- MAGIC External Location
-- MAGIC   READ FILES              -> read files/tables/volumes under this path
-- MAGIC   WRITE FILES             -> write files/tables/volumes under this path
-- MAGIC   CREATE EXTERNAL TABLE   -> register external tables under this path
-- MAGIC   CREATE EXTERNAL VOLUME  -> register external volumes under this path
-- MAGIC ```
-- MAGIC
-- MAGIC The two layers are independent: a data engineer can have full `READ FILES`/
-- MAGIC `WRITE FILES` on an external location for their daily work without ever
-- MAGIC being able to create a *new* external location from that credential, and a
-- MAGIC platform admin with `CREATE EXTERNAL LOCATION` on the credential gets no
-- MAGIC automatic file access on the locations other people create from it.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Required permission on the storage credential
-- MAGIC
-- MAGIC To create an external location using a storage credential (Layer 1 from
-- MAGIC Section 8), the user needs `CREATE EXTERNAL LOCATION` on that credential.
-- MAGIC
-- MAGIC Do not run this unless you are allowed to manage Unity Catalog permissions.

-- COMMAND ----------

-- GRANT CREATE EXTERNAL LOCATION
-- ON STORAGE CREDENTIAL `databricks-course-sc`
-- TO `data-admins`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Create an external location
-- MAGIC
-- MAGIC An external location maps a cloud storage path to a Unity Catalog storage
-- MAGIC credential.
-- MAGIC
-- MAGIC External location name:
-- MAGIC
-- MAGIC ```text
-- MAGIC databricks_course_ext_dl1_demo
-- MAGIC ```
-- MAGIC
-- MAGIC Storage path:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/
-- MAGIC ```
-- MAGIC
-- MAGIC Storage credential:
-- MAGIC
-- MAGIC ```text
-- MAGIC databricks-course-sc
-- MAGIC ```

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS databricks_course_ext_dl1_demo
URL 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL `databricks-course-sc`)
COMMENT 'External location for the demo container';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 11. Show external locations
-- MAGIC
-- MAGIC This lists external locations visible to you.

-- COMMAND ----------

SHOW EXTERNAL LOCATIONS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 12. Describe the external location
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
-- MAGIC ## 13. Show grants on the external location
-- MAGIC
-- MAGIC This may fail if you do not have permission to inspect grants.

-- COMMAND ----------

SHOW GRANTS ON EXTERNAL LOCATION databricks_course_ext_dl1_demo;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 14. Grant access to the external location
-- MAGIC
-- MAGIC These are the Layer 2 privileges from Section 8 - what everyday users can
-- MAGIC do with a path that already has an external location.
-- MAGIC
-- MAGIC ```text
-- MAGIC READ FILES
-- MAGIC WRITE FILES
-- MAGIC CREATE EXTERNAL TABLE
-- MAGIC CREATE EXTERNAL VOLUME
-- MAGIC ```
-- MAGIC
-- MAGIC Typical read-only file access:
-- MAGIC
-- MAGIC ```text
-- MAGIC READ FILES
-- MAGIC ```
-- MAGIC
-- MAGIC Typical external table creation access:
-- MAGIC
-- MAGIC ```text
-- MAGIC READ FILES
-- MAGIC WRITE FILES
-- MAGIC CREATE EXTERNAL TABLE
-- MAGIC ```
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
-- MAGIC ## 15. List files through the external location path
-- MAGIC
-- MAGIC After the external location exists and the user has `READ FILES`, file
-- MAGIC listing is now governed by Unity Catalog rather than a cluster-level cloud
-- MAGIC identity.
-- MAGIC
-- MAGIC This still uses the cloud URI, but access is controlled by Unity Catalog.

-- COMMAND ----------

LIST 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 16. Create a catalog and schema for external table examples
-- MAGIC
-- MAGIC External tables still live inside a catalog and schema, exactly like
-- MAGIC managed tables - see `01_uc_introduction.py` for that object model.
-- MAGIC
-- MAGIC This section creates a small practice namespace, separate from the
-- MAGIC `learning` schema used in notebooks `01`-`03`, to keep managed and external
-- MAGIC examples visually distinct.
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
-- MAGIC ## 17. Create an external table
-- MAGIC
-- MAGIC An external table stores metadata in Unity Catalog, but the data files
-- MAGIC remain in the external cloud storage path - dropping it removes the
-- MAGIC metadata only (Section 21).
-- MAGIC
-- MAGIC Important:
-- MAGIC
-- MAGIC - The `LOCATION` path must be under a registered external location.
-- MAGIC - The user needs `CREATE EXTERNAL TABLE` on that external location.
-- MAGIC - The user also needs `CREATE TABLE` in the target schema.
-- MAGIC
-- MAGIC The following example assumes there is a Delta table folder under:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta
-- MAGIC ```
-- MAGIC
-- MAGIC Do not run unless that folder exists and contains a valid Delta table.

-- COMMAND ----------

-- CREATE TABLE IF NOT EXISTS customers_external
-- LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 18. Create an external table from query output
-- MAGIC
-- MAGIC This creates a new external Delta table at a location under the external
-- MAGIC location.
-- MAGIC
-- MAGIC Use this only if:
-- MAGIC
-- MAGIC - you have `WRITE FILES`
-- MAGIC - you have `CREATE EXTERNAL TABLE`
-- MAGIC - the target path is empty or safe to use
-- MAGIC
-- MAGIC Example output path:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/generated_customers
-- MAGIC ```

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
-- MAGIC ## 19. Query the external table
-- MAGIC
-- MAGIC Uncomment this after creating the external table.

-- COMMAND ----------

-- SELECT *
-- FROM generated_customers_external;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 20. Create an external volume
-- MAGIC
-- MAGIC External volumes are Unity Catalog objects for governing non-tabular files
-- MAGIC that live in cloud storage you already own, as opposed to the managed
-- MAGIC volume created in `01_uc_introduction.py` Section 14.
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
-- MAGIC The external volume path must be under the external location, and the user
-- MAGIC needs `CREATE EXTERNAL VOLUME` on that external location.
-- MAGIC
-- MAGIC Example volume path:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/volumes/demo_files
-- MAGIC ```

-- COMMAND ----------

-- CREATE EXTERNAL VOLUME IF NOT EXISTS demo_files_volume
-- LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/volumes/demo_files'
-- COMMENT 'External volume for demo files';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 21. List files in an external volume
-- MAGIC
-- MAGIC Unity Catalog volume paths use this format regardless of managed vs.
-- MAGIC external:
-- MAGIC
-- MAGIC ```text
-- MAGIC /Volumes/catalog/schema/volume/
-- MAGIC ```
-- MAGIC
-- MAGIC Uncomment after creating the external volume.

-- COMMAND ----------

-- LIST '/Volumes/dev_catalog/external_storage/demo_files_volume/';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 22. Read files directly from the external location
-- MAGIC
-- MAGIC If files exist and you have `READ FILES` on the covering external
-- MAGIC location, you can query them directly by path without registering a table
-- MAGIC at all - useful for one-off exploration of raw files.
-- MAGIC
-- MAGIC Example for CSV files. Uncomment and adjust the path if a CSV file exists.

-- COMMAND ----------

-- SELECT *
-- FROM csv.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/files/customers.csv`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Example for Parquet files. Uncomment and adjust the path if Parquet files exist.

-- COMMAND ----------

-- SELECT *
-- FROM parquet.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/files/customers_parquet/`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Example for Delta files. Uncomment and adjust the path if a Delta table
-- MAGIC exists at the path.

-- COMMAND ----------

-- SELECT *
-- FROM delta.`abfss://demo@databrickscourseextdl1.dfs.core.windows.net/tables/customers_delta/`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 23. Credential vending and Lakehouse Federation, briefly
-- MAGIC
-- MAGIC Two related terms you will run into once you're comfortable with storage
-- MAGIC credentials and external locations - just enough to recognize them, since
-- MAGIC this notebook's job is external storage specifically:
-- MAGIC
-- MAGIC - **Credential vending** is how Unity Catalog hands out short-lived,
-- MAGIC   narrowly-scoped cloud credentials (via its REST API - the same mechanism
-- MAGIC   used by the Iceberg REST catalog endpoint) to engines that are not a
-- MAGIC   Databricks cluster - for example DuckDB, Apache Spark running elsewhere,
-- MAGIC   or another Iceberg/Delta client - so they can read or write a specific
-- MAGIC   table or path directly, without ever being handed a standing storage
-- MAGIC   credential or account key.
-- MAGIC - **Lakehouse Federation** is a different Unity Catalog object,
-- MAGIC   `CREATE CONNECTION`, that lets you query a live external database - MySQL,
-- MAGIC   PostgreSQL, SQL Server, Snowflake, Redshift, BigQuery, and others -
-- MAGIC   directly from Databricks, exposed as a **foreign catalog**, without
-- MAGIC   copying the data in first. It solves a different problem than storage
-- MAGIC   credentials/external locations: federation reaches into another
-- MAGIC   *database*, external locations reach into raw *cloud storage*.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 24. Common errors
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
-- MAGIC Possible causes (check which of the two layers from Section 8 is missing):
-- MAGIC
-- MAGIC - missing `READ FILES` / `WRITE FILES` / `CREATE EXTERNAL TABLE` /
-- MAGIC   `CREATE EXTERNAL VOLUME` on the **external location**
-- MAGIC - missing `CREATE EXTERNAL LOCATION` on the **storage credential**, if you
-- MAGIC   are trying to create a new external location rather than use an existing one
-- MAGIC - missing schema-level privileges (`CREATE TABLE`, `CREATE VOLUME`)
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
-- MAGIC - the Access Connector for Azure Databricks (or service principal) does not
-- MAGIC   have the required Azure RBAC role on the storage account
-- MAGIC - storage account firewall or private-networking configuration blocks the
-- MAGIC   workspace
-- MAGIC - wrong container or storage account name
-- MAGIC - the storage account does not have the hierarchical namespace (HNS)
-- MAGIC   feature enabled, so it isn't really ADLS Gen2
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
-- MAGIC ## 25. Cleanup
-- MAGIC
-- MAGIC Run only if you want to delete the practice objects.
-- MAGIC
-- MAGIC Be careful:
-- MAGIC
-- MAGIC - Dropping an external table removes table metadata only; it does not
-- MAGIC   delete the underlying external data files.
-- MAGIC - Dropping an external location removes the Unity Catalog object, not the
-- MAGIC   cloud storage container.
-- MAGIC - Dropping a storage credential can break every external location that
-- MAGIC   uses it.

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
-- MAGIC - how Unity Catalog governs external cloud storage on Azure
-- MAGIC - what ADLS Gen2's hierarchical namespace is, and why it's required for
-- MAGIC   `abfss://` paths
-- MAGIC - what a storage credential is, and how the Access Connector for Azure
-- MAGIC   Databricks backs it with a managed identity
-- MAGIC - what an external location is, and how to create one for Azure ADLS Gen2
-- MAGIC - the two-layer permission model: `CREATE EXTERNAL LOCATION` on the
-- MAGIC   storage credential versus `READ FILES`/`WRITE FILES`/
-- MAGIC   `CREATE EXTERNAL TABLE`/`CREATE EXTERNAL VOLUME` on the external location
-- MAGIC - how to create external tables and external volumes
-- MAGIC - what credential vending and Lakehouse Federation connections are for, at a
-- MAGIC   recognize-the-term level
-- MAGIC - how to troubleshoot common permission and path errors
-- MAGIC
-- MAGIC Core model:
-- MAGIC
-- MAGIC ```text
-- MAGIC Cloud identity (managed identity via Access Connector, or service principal)
-- MAGIC   -> Storage Credential
-- MAGIC      -> External Location
-- MAGIC         -> READ FILES / WRITE FILES / CREATE EXTERNAL TABLE / CREATE EXTERNAL VOLUME
-- MAGIC         -> External Tables
-- MAGIC         -> External Volumes
-- MAGIC ```
-- MAGIC
-- MAGIC Continue in this folder with:
-- MAGIC
-- MAGIC - `01_uc_introduction.py` - the full object model, in Python and SQL
-- MAGIC - `02_uc_setup_concepts.py` - the admin-vs-user setup boundary in depth
-- MAGIC - `03_sql_introduction-to-unity-catalog.sql` - functions, comments/tags, and
-- MAGIC   Delta Sharing, in pure SQL
