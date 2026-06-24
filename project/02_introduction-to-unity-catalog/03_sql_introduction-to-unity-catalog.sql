-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Unity Catalog in Databricks — SQL Tutorial
-- MAGIC
-- MAGIC This notebook explains how to check, understand, and use Unity Catalog from a Databricks SQL notebook.
-- MAGIC
-- MAGIC There are two different meanings when people say:
-- MAGIC
-- MAGIC **"Create Unity Catalog"**
-- MAGIC
-- MAGIC 1. **Create or enable the Unity Catalog metastore**
-- MAGIC    - Admin-level setup.
-- MAGIC    - Usually done in the Databricks Account Console.
-- MAGIC    - Required before a workspace can use Unity Catalog.
-- MAGIC
-- MAGIC 2. **Create a catalog inside Unity Catalog**
-- MAGIC    - User-level SQL operation.
-- MAGIC    - Done after the workspace is already attached to a Unity Catalog metastore.
-- MAGIC
-- MAGIC Unity Catalog hierarchy:
-- MAGIC
-- MAGIC `text -- MAGIC Metastore -- MAGIC   Catalog -- MAGIC     Schema -- MAGIC       Table -- MAGIC       View -- MAGIC       Volume -- MAGIC `
-- MAGIC
-- MAGIC Fully qualified object name:
-- MAGIC
-- MAGIC `text -- MAGIC catalog.schema.table -- MAGIC `

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
-- MAGIC Example:
-- MAGIC
-- MAGIC `text -- MAGIC dev_catalog -- MAGIC main -- MAGIC samples -- MAGIC `

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
-- MAGIC `text -- MAGIC dev_catalog.learning -- MAGIC `

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
-- MAGIC `text -- MAGIC dev_catalog.learning.customers -- MAGIC `

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
-- MAGIC `text -- MAGIC catalog.schema.table -- MAGIC `

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
-- MAGIC `text -- MAGIC USE CATALOG on the catalog -- MAGIC USE SCHEMA on the schema -- MAGIC SELECT on the table or view -- MAGIC `

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
-- MAGIC Volumes are Unity Catalog objects for files.
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
-- MAGIC `text -- MAGIC /Volumes/catalog/schema/volume/ -- MAGIC `

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
-- MAGIC ## 27. Admin setup versus user setup
-- MAGIC
-- MAGIC Admin setup:
-- MAGIC
-- MAGIC `text -- MAGIC Create Unity Catalog metastore -- MAGIC Assign metastore to workspace -- MAGIC Configure managed storage -- MAGIC Configure identities and groups -- MAGIC `
-- MAGIC
-- MAGIC User setup:
-- MAGIC
-- MAGIC `text -- MAGIC Create catalog -- MAGIC Create schema -- MAGIC Create table -- MAGIC Create view -- MAGIC Create volume -- MAGIC Grant permissions -- MAGIC Query data -- MAGIC `

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 28. Required permissions
-- MAGIC
-- MAGIC To create and query Unity Catalog objects, you need privileges.
-- MAGIC
-- MAGIC Typical permissions:
-- MAGIC
-- MAGIC `text -- MAGIC Metastore: -- MAGIC   CREATE CATALOG -- MAGIC -- MAGIC Catalog: -- MAGIC   USE CATALOG -- MAGIC   CREATE SCHEMA -- MAGIC -- MAGIC Schema: -- MAGIC   USE SCHEMA -- MAGIC   CREATE TABLE -- MAGIC   CREATE VIEW -- MAGIC   CREATE VOLUME -- MAGIC -- MAGIC Table or view: -- MAGIC   SELECT -- MAGIC   MODIFY -- MAGIC `

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 29. Common errors
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
-- MAGIC `text -- MAGIC catalog.schema.table -- MAGIC `

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 30. Cleanup
-- MAGIC
-- MAGIC Run this section only if you want to delete the practice objects.

-- COMMAND ----------

-- DROP VIEW IF EXISTS order_summary_public;

-- COMMAND ----------

-- DROP TABLE IF EXISTS orders;

-- COMMAND ----------

-- DROP VIEW IF EXISTS uk_customers;

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
-- MAGIC - the difference between creating a metastore and creating a catalog
-- MAGIC - how to create a catalog
-- MAGIC - how to create a schema
-- MAGIC - how to create managed tables
-- MAGIC - how to create views
-- MAGIC - how to inspect grants
-- MAGIC - how to create volumes
-- MAGIC - how to query Unity Catalog metadata
-- MAGIC - how to clean up practice objects
-- MAGIC
-- MAGIC Core mental model:
-- MAGIC
-- MAGIC `text -- MAGIC Admin enables Unity Catalog by creating or assigning a metastore. -- MAGIC Users work inside Unity Catalog by creating catalogs, schemas, tables, views, and volumes. -- MAGIC `
