# Databricks notebook source

# MAGIC %md
# MAGIC # Unity Catalog in Databricks
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC This notebook teaches the practical Unity Catalog workflow in Databricks.
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Unity Catalog object hierarchy:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC Metastore
# MAGIC 
# MAGIC   Catalog
# MAGIC 
# MAGIC     Schema
# MAGIC 
# MAGIC       Table
# MAGIC 
# MAGIC       View
# MAGIC 
# MAGIC       Volume
# MAGIC 
# MAGIC ```
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Fully qualified table name:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC catalog.schema.table
# MAGIC 
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Check whether this workspace is attached to a Unity Catalog metastore
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC If this returns a value, Unity Catalog is enabled for this workspace.
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC If it returns `NULL` or fails, the workspace is probably not attached to a Unity Catalog metastore.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_metastore();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Check current catalog and schema

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog();

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_schema();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Show available catalogs
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC A catalog is the first-level namespace under the Unity Catalog metastore.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create a catalog
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC This requires permission to create catalogs on the metastore.
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Replace `dev_catalog` with your preferred catalog name.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog
# MAGIC 
# MAGIC COMMENT 'Development catalog for Unity Catalog learning';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Use the catalog

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG dev_catalog;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Create a schema
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC A schema is the second-level namespace inside a catalog.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS learning
# MAGIC 
# MAGIC COMMENT 'Schema for learning Unity Catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC USE SCHEMA learning;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog(), current_schema();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Create a managed table
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC This creates a Unity Catalog managed table:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC dev_catalog.learning.demo_customers
# MAGIC 
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE demo_customers (
# MAGIC 
# MAGIC   customer_id INT,
# MAGIC 
# MAGIC   customer_name STRING,
# MAGIC 
# MAGIC   country STRING,
# MAGIC 
# MAGIC   created_at DATE
# MAGIC 
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO demo_customers VALUES
# MAGIC 
# MAGIC   (1, 'Ada Lovelace', 'UK', DATE '2026-01-01'),
# MAGIC 
# MAGIC   (2, 'Alan Turing', 'UK', DATE '2026-01-02'),
# MAGIC 
# MAGIC   (3, 'Grace Hopper', 'US', DATE '2026-01-03');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Query with fully qualified name
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Prefer this form in production code:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC catalog.schema.table
# MAGIC 
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM dev_catalog.learning.demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Inspect table metadata

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE demo_customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE EXTENDED demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Show tables in the current schema

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Create a view
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Views are also governed Unity Catalog objects.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW uk_customers AS
# MAGIC 
# MAGIC SELECT
# MAGIC 
# MAGIC   customer_id,
# MAGIC 
# MAGIC   customer_name,
# MAGIC 
# MAGIC   country
# MAGIC 
# MAGIC FROM demo_customers
# MAGIC 
# MAGIC WHERE country = 'UK';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM uk_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Show permissions
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC These commands may fail if you do not have permission to inspect grants.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW GRANTS ON CATALOG dev_catalog;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW GRANTS ON SCHEMA dev_catalog.learning;

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW GRANTS ON TABLE dev_catalog.learning.demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Example permission grants
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Do not run these unless you are allowed to manage access.
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Replace `data-users` with a real Databricks group.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GRANT USE CATALOG ON CATALOG dev_catalog TO `data-users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GRANT USE SCHEMA ON SCHEMA dev_catalog.learning TO `data-users`;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- GRANT SELECT ON TABLE dev_catalog.learning.demo_customers TO `data-users`;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Create a volume
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Volumes are Unity Catalog objects for files.
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Volume path format:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC /Volumes/catalog/schema/volume/
# MAGIC 
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS demo_volume
# MAGIC 
# MAGIC COMMENT 'Managed volume for Unity Catalog learning';

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW VOLUMES;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE VOLUME demo_volume;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. List files in the volume

# COMMAND ----------

# MAGIC %sql
# MAGIC LIST '/Volumes/dev_catalog/learning/demo_volume/';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 16. Use information schema
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Unity Catalog metadata can be queried through `system.information_schema`.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM system.information_schema.catalogs;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM system.information_schema.schemata
# MAGIC 
# MAGIC WHERE catalog_name = 'dev_catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM system.information_schema.tables
# MAGIC 
# MAGIC WHERE table_catalog = 'dev_catalog'
# MAGIC 
# MAGIC   AND table_schema = 'learning';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM system.information_schema.columns
# MAGIC 
# MAGIC WHERE table_catalog = 'dev_catalog'
# MAGIC 
# MAGIC   AND table_schema = 'learning'
# MAGIC 
# MAGIC   AND table_name = 'demo_customers';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 17. Create a second table for practice

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE demo_orders (
# MAGIC 
# MAGIC   order_id INT,
# MAGIC 
# MAGIC   customer_id INT,
# MAGIC 
# MAGIC   order_amount DECIMAL(10, 2),
# MAGIC 
# MAGIC   order_date DATE
# MAGIC 
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO demo_orders VALUES
# MAGIC 
# MAGIC   (101, 1, 120.50, DATE '2026-02-01'),
# MAGIC 
# MAGIC   (102, 1, 75.00, DATE '2026-02-02'),
# MAGIC 
# MAGIC   (103, 2, 210.99, DATE '2026-02-03'),
# MAGIC 
# MAGIC   (104, 3, 49.90, DATE '2026-02-04'),
# MAGIC 
# MAGIC   (105, 3, 300.00, DATE '2026-02-05');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC 
# MAGIC   c.customer_id,
# MAGIC 
# MAGIC   c.customer_name,
# MAGIC 
# MAGIC   c.country,
# MAGIC 
# MAGIC   o.order_id,
# MAGIC 
# MAGIC   o.order_amount,
# MAGIC 
# MAGIC   o.order_date
# MAGIC 
# MAGIC FROM demo_customers c
# MAGIC 
# MAGIC JOIN demo_orders o
# MAGIC 
# MAGIC   ON c.customer_id = o.customer_id;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 18. Create a governed summary view

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW order_summary_public AS
# MAGIC 
# MAGIC SELECT
# MAGIC 
# MAGIC   c.customer_id,
# MAGIC 
# MAGIC   c.country,
# MAGIC 
# MAGIC   COUNT(o.order_id) AS order_count,
# MAGIC 
# MAGIC   SUM(o.order_amount) AS total_order_amount
# MAGIC 
# MAGIC FROM demo_customers c
# MAGIC 
# MAGIC JOIN demo_orders o
# MAGIC 
# MAGIC   ON c.customer_id = o.customer_id
# MAGIC 
# MAGIC GROUP BY
# MAGIC 
# MAGIC   c.customer_id,
# MAGIC 
# MAGIC   c.country;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC 
# MAGIC FROM order_summary_public;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 19. Cleanup
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Run only if you want to delete the practice objects.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP VIEW IF EXISTS order_summary_public;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP TABLE IF EXISTS demo_orders;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP VIEW IF EXISTS uk_customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP TABLE IF EXISTS demo_customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP VOLUME IF EXISTS demo_volume;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP SCHEMA IF EXISTS dev_catalog.learning CASCADE;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- DROP CATALOG IF EXISTS dev_catalog CASCADE;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC You learned:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC - how to check Unity Catalog metastore attachment
# MAGIC 
# MAGIC - how to create a catalog
# MAGIC 
# MAGIC - how to create a schema
# MAGIC 
# MAGIC - how to create managed tables
# MAGIC 
# MAGIC - how to create views
# MAGIC 
# MAGIC - how to inspect grants
# MAGIC 
# MAGIC - how to create volumes
# MAGIC 
# MAGIC - how to query Unity Catalog metadata
# MAGIC 
# MAGIC - how to clean up practice objects
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC Core model:
# MAGIC 
# MAGIC 
# MAGIC 
# MAGIC ```text
# MAGIC 
# MAGIC metastore -> catalog -> schema -> table/view/volume
# MAGIC 
# MAGIC ```
