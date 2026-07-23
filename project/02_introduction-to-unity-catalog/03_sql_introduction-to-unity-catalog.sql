-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Unity Catalog in Databricks — SQL Tutorial
-- MAGIC
-- MAGIC This is the pure-SQL companion to `01_uc_introduction.py` in this same
-- MAGIC folder: the same `dev_catalog.learning` objects, the same day-to-day
-- MAGIC workflow, but written entirely in `.sql` notebook cells with no Python at
-- MAGIC all. See `01_uc_introduction.py` for the full explanation of what Unity
-- MAGIC Catalog is and its complete object model (metastore, catalog, schema,
-- MAGIC table, view, function, volume, storage credential, external location,
-- MAGIC connection, share/recipient/provider) - this notebook goes straight to the
-- MAGIC SQL, plus three topics that notebook doesn't cover in depth: **functions**
-- MAGIC as a securable object, **comments and tags**, and **Delta Sharing** at a
-- MAGIC conceptual level.
-- MAGIC
-- MAGIC For the admin-versus-user distinction (who creates a metastore vs. who
-- MAGIC creates a catalog), see `02_uc_setup_concepts.py`. For external cloud
-- MAGIC storage (storage credentials, external locations, external tables and
-- MAGIC volumes over ADLS Gen2), see `04_sql_configure-access-to-cloud-storage.sql`.
-- MAGIC
-- MAGIC Unity Catalog hierarchy:
-- MAGIC
-- MAGIC ```text
-- MAGIC Metastore
-- MAGIC   Catalog
-- MAGIC     Schema
-- MAGIC       Table
-- MAGIC       View
-- MAGIC       Function
-- MAGIC       Volume
-- MAGIC ```
-- MAGIC
-- MAGIC Fully qualified object name:
-- MAGIC
-- MAGIC ```text
-- MAGIC catalog.schema.table
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Check whether the workspace is attached to a Unity Catalog metastore
-- MAGIC
-- MAGIC A Unity Catalog metastore is the top-level governance container.
-- MAGIC
-- MAGIC If this query returns a value, the workspace is attached to a Unity Catalog metastore.
-- MAGIC
-- MAGIC If it returns `NULL` or fails, Unity Catalog is probably not enabled for this workspace.

-- COMMAND ----------

SELECT current_metastore();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Check the current catalog
-- MAGIC
-- MAGIC A catalog is the first-level namespace under the Unity Catalog metastore.
-- MAGIC
-- MAGIC Example catalogs you will typically see:
-- MAGIC
-- MAGIC ```text
-- MAGIC dev_catalog
-- MAGIC main
-- MAGIC samples
-- MAGIC ```

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Check the current schema
-- MAGIC
-- MAGIC A schema is the second-level namespace inside a catalog.
-- MAGIC
-- MAGIC Tables, views, functions, models, and volumes are created inside schemas.

-- COMMAND ----------

SELECT current_schema();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Show available catalogs
-- MAGIC
-- MAGIC This lists the catalogs you can see.
-- MAGIC
-- MAGIC If a catalog does not appear, you may not have `USE CATALOG` permission on it.

-- COMMAND ----------

SHOW CATALOGS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Create a catalog
-- MAGIC
-- MAGIC This creates a new catalog inside Unity Catalog.
-- MAGIC
-- MAGIC This command may fail if you do not have permission to create catalogs.
-- MAGIC
-- MAGIC Replace `dev_catalog` with your own catalog name if needed.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS dev_catalog
COMMENT 'Development catalog for learning Unity Catalog';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Use the catalog
-- MAGIC
-- MAGIC This sets the current catalog for the notebook session.

-- COMMAND ----------

USE CATALOG dev_catalog;

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Create a schema
-- MAGIC
-- MAGIC A schema groups tables, views, functions, and volumes inside a catalog.
-- MAGIC
-- MAGIC The full schema name is:
-- MAGIC
-- MAGIC ```text
-- MAGIC dev_catalog.learning
-- MAGIC ```

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS learning
COMMENT 'Schema for Unity Catalog learning';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Use the schema
-- MAGIC
-- MAGIC This sets the current schema inside the current catalog.

-- COMMAND ----------

USE SCHEMA learning;

-- COMMAND ----------

SELECT current_catalog(), current_schema();

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Create a managed table
-- MAGIC
-- MAGIC This creates a managed table in Unity Catalog.
-- MAGIC
-- MAGIC Full table name:
-- MAGIC
-- MAGIC ```text
-- MAGIC dev_catalog.learning.customers
-- MAGIC ```

-- COMMAND ----------

CREATE OR REPLACE TABLE customers (
customer_id INT,
customer_name STRING,
country STRING,
created_at DATE
);

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 10. Insert sample data

-- COMMAND ----------

INSERT INTO customers VALUES
(1, 'Ada Lovelace', 'UK', DATE '2026-01-01'),
(2, 'Alan Turing', 'UK', DATE '2026-01-02'),
(3, 'Grace Hopper', 'US', DATE '2026-01-03');

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 11. Query the table

-- COMMAND ----------

SELECT *
FROM customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 12. Query the table with a fully qualified name
-- MAGIC
-- MAGIC In production code, prefer the full name:
-- MAGIC
-- MAGIC ```text
-- MAGIC catalog.schema.table
-- MAGIC ```

-- COMMAND ----------

SELECT *
FROM dev_catalog.learning.customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 13. Describe the table
-- MAGIC
-- MAGIC This shows column information.

-- COMMAND ----------

DESCRIBE TABLE customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 14. Describe extended table metadata
-- MAGIC
-- MAGIC This shows more metadata, including ownership and storage-related details.
-- MAGIC Check the `Type` field (`MANAGED` here) and the `Location` field, which
-- MAGIC points inside the schema's managed storage location.

-- COMMAND ----------

DESCRIBE TABLE EXTENDED customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 15. Show tables in the current schema

-- COMMAND ----------

SHOW TABLES;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 16. Create a view
-- MAGIC
-- MAGIC Views are governed objects in Unity Catalog.
-- MAGIC
-- MAGIC You can grant access to a view instead of granting access to the underlying table.

-- COMMAND ----------

CREATE OR REPLACE VIEW uk_customers AS
SELECT
customer_id,
customer_name,
country
FROM customers
WHERE country = 'UK';

-- COMMAND ----------

SELECT *
FROM uk_customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 17. Create a second table
-- MAGIC
-- MAGIC This table will be used for a join example.

-- COMMAND ----------

CREATE OR REPLACE TABLE orders (
order_id INT,
customer_id INT,
order_amount DECIMAL(10, 2),
order_date DATE
);

-- COMMAND ----------

INSERT INTO orders VALUES
(101, 1, 120.50, DATE '2026-02-01'),
(102, 1, 75.00, DATE '2026-02-02'),
(103, 2, 210.99, DATE '2026-02-03'),
(104, 3, 49.90, DATE '2026-02-04'),
(105, 3, 300.00, DATE '2026-02-05');

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 18. Join tables inside Unity Catalog

-- COMMAND ----------

SELECT
c.customer_id,
c.customer_name,
c.country,
o.order_id,
o.order_amount,
o.order_date
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 19. Create a governed summary view
-- MAGIC
-- MAGIC This view hides customer names and exposes only aggregated business data.

-- COMMAND ----------

CREATE OR REPLACE VIEW order_summary_public AS
SELECT
c.customer_id,
c.country,
COUNT(o.order_id) AS order_count,
SUM(o.order_amount) AS total_order_amount
FROM customers c
JOIN orders o
ON c.customer_id = o.customer_id
GROUP BY
c.customer_id,
c.country;

-- COMMAND ----------

SELECT *
FROM order_summary_public;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 20. Show grants on the catalog
-- MAGIC
-- MAGIC This may fail if you do not have permission to inspect grants.

-- COMMAND ----------

SHOW GRANTS ON CATALOG dev_catalog;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 21. Show grants on the schema
-- MAGIC
-- MAGIC This may fail if you do not have permission to inspect grants.

-- COMMAND ----------

SHOW GRANTS ON SCHEMA dev_catalog.learning;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 22. Show grants on a table
-- MAGIC
-- MAGIC This may fail if you do not have permission to inspect grants.

-- COMMAND ----------

SHOW GRANTS ON TABLE dev_catalog.learning.customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 23. Example grants
-- MAGIC
-- MAGIC Do not run these unless you are allowed to manage permissions.
-- MAGIC
-- MAGIC Replace `data-users` with a real Databricks group.
-- MAGIC
-- MAGIC Typical read access requires:
-- MAGIC
-- MAGIC ```text
-- MAGIC USE CATALOG on the catalog
-- MAGIC USE SCHEMA on the schema
-- MAGIC SELECT on the table or view
-- MAGIC ```

-- COMMAND ----------

-- GRANT USE CATALOG ON CATALOG dev_catalog TO `data-users`;

-- COMMAND ----------

-- GRANT USE SCHEMA ON SCHEMA dev_catalog.learning TO `data-users`;

-- COMMAND ----------

-- GRANT SELECT ON TABLE dev_catalog.learning.customers TO `data-users`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 24. Create a volume
-- MAGIC
-- MAGIC Volumes are Unity Catalog objects for files - see `01_uc_introduction.py`
-- MAGIC Section 14 for the managed-vs-external distinction. This creates a managed
-- MAGIC volume.
-- MAGIC
-- MAGIC Use volumes for:
-- MAGIC
-- MAGIC - CSV files
-- MAGIC - JSON files
-- MAGIC - images
-- MAGIC - model artifacts
-- MAGIC - configuration files
-- MAGIC
-- MAGIC Volume path format:
-- MAGIC
-- MAGIC ```text
-- MAGIC /Volumes/catalog/schema/volume/
-- MAGIC ```

-- COMMAND ----------

CREATE VOLUME IF NOT EXISTS demo_volume
COMMENT 'Managed volume for Unity Catalog learning';

-- COMMAND ----------

SHOW VOLUMES;

-- COMMAND ----------

DESCRIBE VOLUME demo_volume;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 25. List files in the volume
-- MAGIC
-- MAGIC This works after files exist in the volume.

-- COMMAND ----------

LIST '/Volumes/dev_catalog/learning/demo_volume/';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 26. Query Unity Catalog metadata
-- MAGIC
-- MAGIC Unity Catalog exposes metadata through `system.information_schema`.

-- COMMAND ----------

SELECT *
FROM system.information_schema.catalogs;

-- COMMAND ----------

SELECT *
FROM system.information_schema.schemata
WHERE catalog_name = 'dev_catalog';

-- COMMAND ----------

SELECT *
FROM system.information_schema.tables
WHERE table_catalog = 'dev_catalog'
AND table_schema = 'learning';

-- COMMAND ----------

SELECT *
FROM system.information_schema.columns
WHERE table_catalog = 'dev_catalog'
AND table_schema = 'learning'
AND table_name = 'customers';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 27. Functions as a securable object
-- MAGIC
-- MAGIC Unity Catalog governs SQL functions the same way it governs tables and
-- MAGIC views: a function lives at `catalog.schema.function_name`, has an owner,
-- MAGIC can be documented with a comment, and requires an explicit `EXECUTE` grant
-- MAGIC before another principal can call it.
-- MAGIC
-- MAGIC This creates a small scalar SQL function that expands the two-letter
-- MAGIC country codes already used in `customers`.

-- COMMAND ----------

CREATE OR REPLACE FUNCTION dev_catalog.learning.country_label(country_code STRING)
RETURNS STRING
COMMENT 'Expands a two-letter country code from customers.country into a display label'
RETURN CASE country_code
  WHEN 'UK' THEN 'United Kingdom'
  WHEN 'US' THEN 'United States'
  ELSE country_code
END;

-- COMMAND ----------

SELECT
  customer_id,
  customer_name,
  country,
  dev_catalog.learning.country_label(country) AS country_label
FROM customers;

-- COMMAND ----------

SHOW FUNCTIONS IN dev_catalog.learning;

-- COMMAND ----------

DESCRIBE FUNCTION EXTENDED dev_catalog.learning.country_label;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Grants on a function work exactly like grants on a table - do not run this
-- MAGIC unless you are allowed to manage permissions.

-- COMMAND ----------

SHOW GRANTS ON FUNCTION dev_catalog.learning.country_label;

-- COMMAND ----------

-- GRANT EXECUTE ON FUNCTION dev_catalog.learning.country_label TO `data-users`;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 28. Document objects with comments and tags
-- MAGIC
-- MAGIC See `01_uc_introduction.py` Section 16 for why this matters - in short, it
-- MAGIC keeps Catalog Explorer search useful as the catalog grows. Here are just the
-- MAGIC commands, applied to this notebook's own table.

-- COMMAND ----------

COMMENT ON TABLE dev_catalog.learning.customers IS
'Practice customer dimension for the Unity Catalog SQL learning module';

-- COMMAND ----------

ALTER TABLE dev_catalog.learning.customers
ALTER COLUMN country COMMENT 'Free-text country label used for practice data only, not validated against ISO codes';

-- COMMAND ----------

ALTER TABLE dev_catalog.learning.customers
SET TBLPROPERTIES ('data_owner' = 'data-engineering-training', 'pii' = 'false');

-- COMMAND ----------

-- Newer Databricks Runtime versions also support governed, searchable tags
-- (distinct from free-form TBLPROPERTIES) on catalogs, schemas, tables, and
-- columns, if tags are enabled for your metastore:
-- ALTER TABLE dev_catalog.learning.customers SET TAGS ('sensitivity' = 'low');

-- COMMAND ----------

DESCRIBE TABLE EXTENDED customers;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 29. Delta Sharing, conceptually
-- MAGIC
-- MAGIC Delta Sharing is Unity Catalog's mechanism for sharing live tables, views,
-- MAGIC and volumes with recipients **outside** your Databricks account or
-- MAGIC metastore, without copying any data. Three objects are involved:
-- MAGIC
-- MAGIC - **Share** - a named, curated bundle of objects you want to expose.
-- MAGIC - **Recipient** - the consumer: another Databricks account (Unity
-- MAGIC   Catalog-to-Unity-Catalog sharing) or an open recipient authenticated with
-- MAGIC   a downloadable credential file, for non-Databricks consumers.
-- MAGIC - **Provider** - from the recipient's side, the entity that shared data
-- MAGIC   with them.
-- MAGIC
-- MAGIC Creating and managing shares is normally a data-owner or admin task, and
-- MAGIC requires a recipient to already exist on the other side. The statements
-- MAGIC below are illustrative only - do not run them as written.

-- COMMAND ----------

-- CREATE SHARE IF NOT EXISTS learning_share
-- COMMENT 'Illustrative share exposing order_summary_public to a partner';
--
-- ALTER SHARE learning_share ADD TABLE dev_catalog.learning.order_summary_public;
--
-- CREATE RECIPIENT IF NOT EXISTS partner_recipient;
--
-- GRANT SELECT ON SHARE learning_share TO RECIPIENT partner_recipient;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 30. Admin setup versus user setup
-- MAGIC
-- MAGIC Brief recap - see `02_uc_setup_concepts.py` for the full breakdown,
-- MAGIC including the Account Console walkthrough and workspace-catalog bindings.
-- MAGIC
-- MAGIC ```text
-- MAGIC Admin setup (one-time, Account Console):
-- MAGIC   Create Unity Catalog metastore
-- MAGIC   Assign metastore to workspace
-- MAGIC   Configure managed storage
-- MAGIC   Configure identities and groups
-- MAGIC
-- MAGIC User setup (everyday, SQL):
-- MAGIC   Create catalog
-- MAGIC   Create schema
-- MAGIC   Create table, view, function, volume
-- MAGIC   Grant permissions
-- MAGIC   Query data
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 31. Required permissions
-- MAGIC
-- MAGIC To create and query Unity Catalog objects, you need privileges.
-- MAGIC
-- MAGIC Typical permissions:
-- MAGIC
-- MAGIC ```text
-- MAGIC Metastore:
-- MAGIC   CREATE CATALOG
-- MAGIC
-- MAGIC Catalog:
-- MAGIC   USE CATALOG
-- MAGIC   CREATE SCHEMA
-- MAGIC
-- MAGIC Schema:
-- MAGIC   USE SCHEMA
-- MAGIC   CREATE TABLE
-- MAGIC   CREATE VIEW
-- MAGIC   CREATE FUNCTION
-- MAGIC   CREATE VOLUME
-- MAGIC
-- MAGIC Table or view:
-- MAGIC   SELECT
-- MAGIC   MODIFY
-- MAGIC
-- MAGIC Function:
-- MAGIC   EXECUTE
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 32. Common errors
-- MAGIC
-- MAGIC ### Error: `Catalog does not exist`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - wrong catalog name
-- MAGIC - missing `USE CATALOG` permission
-- MAGIC - workspace is not attached to the expected metastore
-- MAGIC
-- MAGIC ### Error: `Permission denied`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - missing `USE CATALOG`
-- MAGIC - missing `USE SCHEMA`
-- MAGIC - missing `SELECT`
-- MAGIC - missing `CREATE TABLE`
-- MAGIC - missing `CREATE CATALOG`
-- MAGIC - missing `EXECUTE` on a function
-- MAGIC
-- MAGIC ### Error: `Table not found`
-- MAGIC
-- MAGIC Possible causes:
-- MAGIC
-- MAGIC - wrong current catalog
-- MAGIC - wrong current schema
-- MAGIC - table exists in another namespace
-- MAGIC
-- MAGIC Use fully qualified names to avoid ambiguity:
-- MAGIC
-- MAGIC ```text
-- MAGIC catalog.schema.table
-- MAGIC ```

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 33. Cleanup
-- MAGIC
-- MAGIC Run this section only if you want to delete the practice objects.

-- COMMAND ----------

-- DROP VIEW IF EXISTS order_summary_public;

-- COMMAND ----------

-- DROP TABLE IF EXISTS orders;

-- COMMAND ----------

-- DROP VIEW IF EXISTS uk_customers;

-- COMMAND ----------

-- DROP FUNCTION IF EXISTS dev_catalog.learning.country_label;

-- COMMAND ----------

-- DROP TABLE IF EXISTS customers;

-- COMMAND ----------

-- DROP VOLUME IF EXISTS demo_volume;

-- COMMAND ----------

-- DROP SCHEMA IF EXISTS dev_catalog.learning CASCADE;

-- COMMAND ----------

-- DROP CATALOG IF EXISTS dev_catalog CASCADE;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary
-- MAGIC
-- MAGIC You learned:
-- MAGIC
-- MAGIC - how to check whether a workspace is attached to a Unity Catalog metastore
-- MAGIC - how to create a catalog, schema, managed table, and view in pure SQL
-- MAGIC - how to inspect and grant permissions on catalogs, schemas, and tables
-- MAGIC - how to create a managed volume
-- MAGIC - how to query Unity Catalog metadata via `system.information_schema`
-- MAGIC - how functions are a governed securable object, with their own owner,
-- MAGIC   comment, and `EXECUTE` privilege
-- MAGIC - how to document objects with `COMMENT ON`, column comments, and
-- MAGIC   `TBLPROPERTIES`
-- MAGIC - what Delta Sharing's Share/Recipient/Provider objects are for, at a
-- MAGIC   conceptual level
-- MAGIC - how to clean up practice objects
-- MAGIC
-- MAGIC Core mental model:
-- MAGIC
-- MAGIC ```text
-- MAGIC Admin enables Unity Catalog by creating or assigning a metastore.
-- MAGIC Users work inside Unity Catalog by creating catalogs, schemas, tables,
-- MAGIC views, functions, and volumes.
-- MAGIC ```
-- MAGIC
-- MAGIC Continue in this folder with:
-- MAGIC
-- MAGIC - `01_uc_introduction.py` - the full object model, in Python and SQL
-- MAGIC - `02_uc_setup_concepts.py` - the admin-vs-user setup boundary in depth
-- MAGIC - `04_sql_configure-access-to-cloud-storage.sql` - storage credentials,
-- MAGIC   external locations, and external tables/volumes over Azure Data Lake
-- MAGIC   Storage
