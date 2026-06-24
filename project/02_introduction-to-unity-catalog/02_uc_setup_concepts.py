# Databricks notebook source

# MAGIC %md

# MAGIC # Unity Catalog Setup Concepts

# MAGIC

# MAGIC This notebook explains what people usually mean when they say:

# MAGIC

# MAGIC > "Create Unity Catalog in Databricks"

# MAGIC

# MAGIC There are two different meanings:

# MAGIC

# MAGIC 1. **Create or enable the Unity Catalog metastore**

# MAGIC    - Admin-level setup.

# MAGIC    - Usually done by an account admin.

# MAGIC    - Makes the workspace Unity Catalog-enabled.

# MAGIC

# MAGIC 2. **Create a catalog inside Unity Catalog**

# MAGIC    - Data-governance object creation.

# MAGIC    - Usually done with SQL.

# MAGIC    - Used by data engineers, analysts, and platform teams after Unity Catalog is enabled.

# MAGIC

# MAGIC Unity Catalog object hierarchy:

# MAGIC

# MAGIC ```text

# MAGIC Metastore

# MAGIC   Catalog

# MAGIC     Schema

# MAGIC       Table

# MAGIC       View

# MAGIC       Volume

# MAGIC ```

# MAGIC

# MAGIC Fully qualified table name:

# MAGIC

# MAGIC ```text

# MAGIC catalog.schema.table

# MAGIC ```

# COMMAND ----------

# MAGIC %md

# MAGIC ## 1. Check whether Unity Catalog is already enabled

# MAGIC

# MAGIC Run this command in a Databricks notebook attached to Unity Catalog-compatible compute.

# MAGIC

# MAGIC If it returns a value, the workspace is attached to a Unity Catalog metastore.

# MAGIC

# MAGIC If it returns `NULL` or fails, the workspace is probably not attached to a Unity Catalog metastore, or the compute is not Unity Catalog-compatible.

# COMMAND ----------

# MAGIC %sql

# MAGIC SELECT current_metastore();

# COMMAND ----------

# MAGIC %md

# MAGIC Example result:

# MAGIC

# MAGIC ```text

# MAGIC aws:eu-west-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# MAGIC ```

# MAGIC

# MAGIC The exact value depends on your cloud, region, and metastore ID.

# COMMAND ----------

# MAGIC %md

# MAGIC ## 2. Admin-level setup: create or enable the Unity Catalog metastore

# MAGIC

# MAGIC This part is usually not done by a normal workspace user.

# MAGIC

# MAGIC It is usually done by:

# MAGIC

# MAGIC - Databricks account admin

# MAGIC - platform admin

# MAGIC - cloud/data platform team

# MAGIC

# MAGIC High-level admin steps:

# MAGIC

# MAGIC 1. Open the **Databricks Account Console**.

# MAGIC 2. Go to **Data** / **Unity Catalog** / **Metastores**.

# MAGIC 3. Create a new metastore if one does not already exist for the region.

# MAGIC 4. Choose the cloud region.

# MAGIC 5. Configure managed storage.

# MAGIC 6. Assign the metastore to one or more workspaces.

# MAGIC 7. Confirm from the workspace with:

# MAGIC

# MAGIC ```sql

# MAGIC SELECT current_metastore();

# MAGIC ```

# MAGIC

# MAGIC Important:

# MAGIC

# MAGIC You do not normally create the Unity Catalog metastore with notebook SQL.

# MAGIC Notebook SQL is normally used after the workspace has already been attached to a metastore.

# COMMAND ----------

# MAGIC %md

# MAGIC ## 3. User-level setup: create a catalog

# MAGIC

# MAGIC After the workspace is attached to a Unity Catalog metastore, users with the correct privileges can create catalogs.

# MAGIC

# MAGIC A catalog is the first level in the namespace:

# MAGIC

# MAGIC ```text

# MAGIC catalog.schema.table

# MAGIC ```

# MAGIC

# MAGIC Example:

# MAGIC

# MAGIC ```text

# MAGIC dev_catalog.learning.customers

# MAGIC ```

# MAGIC

# MAGIC This means:

# MAGIC

# MAGIC - catalog: `dev_catalog`

# MAGIC - schema: `learning`

# MAGIC - table: `customers`

# COMMAND ----------

# MAGIC %sql

# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %md

# MAGIC Create a catalog.

# MAGIC

# MAGIC This may fail if you do not have `CREATE CATALOG` or equivalent metastore-level privileges.

# COMMAND ----------

# MAGIC %sql

# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog

# MAGIC COMMENT 'Development catalog for learning Unity Catalog';

# COMMAND ----------

# MAGIC %md

# MAGIC Use the catalog.

# COMMAND ----------

# MAGIC %sql

# MAGIC USE CATALOG dev_catalog;

# COMMAND ----------

# MAGIC %sql

# MAGIC SELECT current_catalog();

# COMMAND ----------

# MAGIC %md

# MAGIC ## 4. Create a schema inside the catalog

# MAGIC

# MAGIC A schema is the second-level namespace inside a catalog.

# MAGIC

# MAGIC Tables, views, functions, models, and volumes are created inside schemas.

# COMMAND ----------

# MAGIC %sql

# MAGIC CREATE SCHEMA IF NOT EXISTS dev_catalog.learning

# MAGIC COMMENT 'Schema for Unity Catalog practice';

# COMMAND ----------

# MAGIC %sql

# MAGIC USE SCHEMA dev_catalog.learning;

# COMMAND ----------

# MAGIC %sql

# MAGIC SELECT current_catalog(), current_schema();

# COMMAND ----------

# MAGIC %md

# MAGIC ## 5. Create a table inside Unity Catalog

# MAGIC

# MAGIC This creates a managed table:

# MAGIC

# MAGIC ```text

# MAGIC dev_catalog.learning.customers

# MAGIC ```

# COMMAND ----------

# MAGIC %sql

# MAGIC CREATE OR REPLACE TABLE dev_catalog.learning.customers (

# MAGIC   customer_id INT,

# MAGIC   customer_name STRING,

# MAGIC   country STRING

# MAGIC );

# COMMAND ----------

# MAGIC %sql

# MAGIC INSERT INTO dev_catalog.learning.customers VALUES

# MAGIC   (1, 'Ada Lovelace', 'UK'),

# MAGIC   (2, 'Alan Turing', 'UK'),

# MAGIC   (3, 'Grace Hopper', 'US');

# COMMAND ----------

# MAGIC %sql

# MAGIC SELECT *

# MAGIC FROM dev_catalog.learning.customers;

# COMMAND ----------

# MAGIC %md

# MAGIC ## 6. Minimal working notebook flow

# MAGIC

# MAGIC The minimal flow after Unity Catalog is enabled is:

# MAGIC

# MAGIC ```sql

# MAGIC SELECT current_metastore();

# MAGIC

# MAGIC SHOW CATALOGS;

# MAGIC

# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog

# MAGIC COMMENT 'Development catalog for learning Unity Catalog';

# MAGIC

# MAGIC USE CATALOG dev_catalog;

# MAGIC

# MAGIC CREATE SCHEMA IF NOT EXISTS learning

# MAGIC COMMENT 'Learning schema';

# MAGIC

# MAGIC USE SCHEMA learning;

# MAGIC

# MAGIC CREATE OR REPLACE TABLE customers (

# MAGIC   customer_id INT,

# MAGIC   customer_name STRING,

# MAGIC   country STRING

# MAGIC );

# MAGIC

# MAGIC INSERT INTO customers VALUES

# MAGIC   (1, 'Ada Lovelace', 'UK'),

# MAGIC   (2, 'Alan Turing', 'UK'),

# MAGIC   (3, 'Grace Hopper', 'US');

# MAGIC

# MAGIC SELECT *

# MAGIC FROM dev_catalog.learning.customers;

# MAGIC ```

# COMMAND ----------

# MAGIC %md

# MAGIC ## 7. Required permissions

# MAGIC

# MAGIC To create and query Unity Catalog objects, you need privileges.

# MAGIC

# MAGIC Typical privilege chain:

# MAGIC

# MAGIC ```text

# MAGIC Metastore

# MAGIC   CREATE CATALOG

# MAGIC

# MAGIC Catalog

# MAGIC   USE CATALOG

# MAGIC   CREATE SCHEMA

# MAGIC

# MAGIC Schema

# MAGIC   USE SCHEMA

# MAGIC   CREATE TABLE

# MAGIC   CREATE VIEW

# MAGIC   CREATE VOLUME

# MAGIC

# MAGIC Table or View

# MAGIC   SELECT

# MAGIC   MODIFY

# MAGIC ```

# MAGIC

# MAGIC Common read-access pattern:

# MAGIC

# MAGIC ```text

# MAGIC USE CATALOG on catalog

# MAGIC USE SCHEMA on schema

# MAGIC SELECT on table or view

# MAGIC ```

# COMMAND ----------

# MAGIC %md

# MAGIC Example grants.

# MAGIC

# MAGIC Do not run these unless you are allowed to manage permissions.

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

# MAGIC -- GRANT SELECT ON TABLE dev_catalog.learning.customers TO `data-users`;

# COMMAND ----------

# MAGIC %md

# MAGIC ## 8. Inspect grants

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

# MAGIC SHOW GRANTS ON TABLE dev_catalog.learning.customers;

# COMMAND ----------

# MAGIC %md

# MAGIC ## 9. Admin setup vs user setup

# MAGIC

# MAGIC Admin-level setup:

# MAGIC

# MAGIC ```text

# MAGIC Create metastore

# MAGIC Assign metastore to workspace

# MAGIC Configure storage

# MAGIC Configure account-level identities and groups

# MAGIC ```

# MAGIC

# MAGIC User-level setup:

# MAGIC

# MAGIC ```text

# MAGIC Create catalog

# MAGIC Create schema

# MAGIC Create table

# MAGIC Create view

# MAGIC Create volume

# MAGIC Grant access

# MAGIC Query data

# MAGIC ```

# COMMAND ----------

# MAGIC %md

# MAGIC ## 10. Mental model

# MAGIC

# MAGIC You do not usually "create Unity Catalog" with SQL.

# MAGIC

# MAGIC More precise wording:

# MAGIC

# MAGIC ```text

# MAGIC Admin creates or assigns the Unity Catalog metastore.

# MAGIC User creates catalogs, schemas, tables, views, and volumes inside that metastore.

# MAGIC ```

# MAGIC

# MAGIC Practical SQL answer:

# MAGIC

# MAGIC ```sql

# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog;

# MAGIC ```

# MAGIC

# MAGIC Admin-level answer:

# MAGIC

# MAGIC ```text

# MAGIC Account Console

# MAGIC   -> Create Unity Catalog metastore

# MAGIC   -> Assign workspace

# MAGIC   -> Configure storage and permissions

# MAGIC   -> Users create catalogs and schemas

# MAGIC ```

# COMMAND ----------

# MAGIC %md

# MAGIC ## 11. Cleanup

# MAGIC

# MAGIC Run only if you want to remove the practice objects.

# COMMAND ----------

# MAGIC %sql

# MAGIC -- DROP TABLE IF EXISTS dev_catalog.learning.customers;

# COMMAND ----------

# MAGIC %sql

# MAGIC -- DROP SCHEMA IF EXISTS dev_catalog.learning CASCADE;

# COMMAND ----------

# MAGIC %sql

# MAGIC -- DROP CATALOG IF EXISTS dev_catalog CASCADE;
