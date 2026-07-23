# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog in Databricks
# MAGIC
# MAGIC This notebook is a practical, hands-on introduction to Unity Catalog (UC): what it
# MAGIC is, how its objects fit together, and the day-to-day SQL and Python you use once a
# MAGIC workspace is already attached to a metastore.
# MAGIC
# MAGIC ## What is Unity Catalog?
# MAGIC
# MAGIC Unity Catalog is Databricks' centralized governance layer for data and AI assets
# MAGIC across an entire account, not just a single workspace. One **metastore** is
# MAGIC registered per cloud region, and every workspace in that region can attach to it.
# MAGIC Once attached, catalogs, schemas, tables, views, volumes, and the grants on them
# MAGIC are defined **once** and enforced consistently everywhere, instead of being
# MAGIC re-created per workspace the way the legacy Hive metastore worked.
# MAGIC
# MAGIC Concretely, Unity Catalog gives you:
# MAGIC
# MAGIC - One consistent three-level namespace (`catalog.schema.object`) for every table,
# MAGIC   view, volume, function, and registered ML model.
# MAGIC - Centralized, fine-grained access control enforced with standard SQL
# MAGIC   `GRANT`/`REVOKE`, applied consistently across SQL, Python, Scala, R, and
# MAGIC   serverless compute.
# MAGIC - Automatic, column-level **data lineage** captured across notebooks, jobs,
# MAGIC   dashboards, and pipelines - with no extra instrumentation.
# MAGIC - Built-in **auditing**: every query and every grant change is logged.
# MAGIC - Centralized discovery, documentation (comments), and tags via Catalog Explorer.
# MAGIC - Governed data sharing outside your account via **Delta Sharing**, without
# MAGIC   copying data.
# MAGIC
# MAGIC !!! Legacy vs Unity Catalog
# MAGIC
# MAGIC Before Unity Catalog, Databricks relied on the Databricks File System (DBFS) and
# MAGIC a workspace-local Hive metastore. Databricks now treats that combination as
# MAGIC legacy. Azure subscriptions created after November 2023 get a Unity Catalog
# MAGIC metastore created and attached automatically the moment the first workspace is
# MAGIC deployed in a region, so most learners never touch metastore creation directly.
# MAGIC
# MAGIC ## The object model
# MAGIC
# MAGIC ```text
# MAGIC Metastore                     (one per cloud region, account-level)
# MAGIC   Catalog                     (top-level namespace: per domain or per environment)
# MAGIC     Schema                    (a.k.a. database)
# MAGIC       Table    (managed | external)
# MAGIC       View
# MAGIC       Function
# MAGIC       Volume   (managed | external)
# MAGIC   Storage Credential          (cloud identity: managed identity / service principal)
# MAGIC   External Location          (credential + cloud path, backs external tables/volumes)
# MAGIC   Connection                  (Lakehouse Federation: MySQL, Postgres, Snowflake, ...)
# MAGIC   Share / Recipient / Provider (Delta Sharing)
# MAGIC ```
# MAGIC
# MAGIC ### Managed vs external tables and volumes
# MAGIC
# MAGIC | | Managed | External |
# MAGIC | --- | --- | --- |
# MAGIC | Data files owned by | Unity Catalog, under the schema's managed storage location | You - an existing cloud storage path UC only points at |
# MAGIC | Format | Delta Lake only | Any format: Delta, Parquet, CSV, JSON, ... |
# MAGIC | `DROP` | Deletes metadata **and** data files | Deletes metadata only; data is untouched |
# MAGIC | Typical use | Data Databricks fully owns (your bronze/silver/gold tables) | Data produced by another system that Databricks only reads |
# MAGIC
# MAGIC ### Fully qualified names and defaults
# MAGIC
# MAGIC ```text
# MAGIC catalog.schema.table
# MAGIC ```
# MAGIC
# MAGIC New workspaces default to catalog `main` and schema `default`. Older workspaces may
# MAGIC also expose a read-only `hive_metastore` catalog for backward compatibility - it is
# MAGIC not governed by Unity Catalog the same way and should not be used for new work.
# MAGIC
# MAGIC ## 0. How is a Unity Catalog metastore created?
# MAGIC
# MAGIC This is normally a one-time **account-admin** task, done outside of any notebook:
# MAGIC
# MAGIC 1. Sign in to the Databricks Account Console (`accounts.azuredatabricks.net` on
# MAGIC    Azure) as an account admin.
# MAGIC 2. Go to **Catalog** -> **Create metastore**.
# MAGIC 3. Choose a name and a cloud region - the region must match the workspaces you
# MAGIC    plan to attach, and only **one metastore is allowed per region**.
# MAGIC 4. Leave the default storage location blank in most cases. Databricks recommends
# MAGIC    assigning a managed storage location **per catalog or schema** instead, so you
# MAGIC    can scope access and track storage cost per business area rather than
# MAGIC    dumping everything into one container.
# MAGIC 5. Assign your workspace(s) to the metastore and enable it.
# MAGIC 6. Set a metastore admin - ideally a group, never `All users` or a single person.
# MAGIC 7. From a notebook in the attached workspace, confirm with
# MAGIC    `SELECT current_metastore();` (Section 1 below).
# MAGIC
# MAGIC If your Azure subscription was created after November 2023, this already happened
# MAGIC automatically - `current_metastore()` should return an ID with no setup on your
# MAGIC part. See `02_uc_setup_concepts.py` in this same folder for the full admin-vs-user
# MAGIC breakdown, and `docs/06_unity-catalog/` for the account console walkthrough.
# MAGIC
# MAGIC Everything from Section 1 onward is the **user-level** workflow: what you do
# MAGIC inside a notebook once the metastore already exists.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Check whether this workspace is attached to a Unity Catalog metastore
# MAGIC
# MAGIC If this returns a value, Unity Catalog is enabled for this workspace.
# MAGIC
# MAGIC If it returns `NULL` or fails, the workspace is probably not attached to a Unity
# MAGIC Catalog metastore, or the attached compute does not support Unity Catalog (for
# MAGIC example, some legacy no-isolation-shared clusters).

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_metastore();

# COMMAND ----------

# Defensive version of the same check, useful in production code where you don't
# want a missing metastore attachment to crash the whole job with a raw stack trace.
try:
    metastore_id = spark.sql("SELECT current_metastore() AS id").collect()[0]["id"]
    print(f"Attached to Unity Catalog metastore: {metastore_id}")
except Exception as e:
    print("This compute/workspace does not appear to be attached to a Unity Catalog metastore.")
    print(f"Details: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Check the current catalog and schema
# MAGIC
# MAGIC Every session has a current catalog and current schema, used to resolve any
# MAGIC unqualified table name you reference.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog();

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_schema();

# COMMAND ----------

current_catalog = spark.sql("SELECT current_catalog() AS c").collect()[0]["c"]
current_schema = spark.sql("SELECT current_schema() AS s").collect()[0]["s"]

print(f"current_catalog = {current_catalog}")
print(f"current_schema  = {current_schema}")

# On Databricks Runtime 13.3 LTS and above, the native Catalog API offers the same
# information without writing raw SQL strings:
#   spark.catalog.currentCatalog()
#   spark.catalog.setCurrentCatalog("catalog_name")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Show available catalogs
# MAGIC
# MAGIC A catalog is the first-level namespace under the Unity Catalog metastore. Besides
# MAGIC catalogs you create, you will typically also see:
# MAGIC
# MAGIC - `system` - Unity Catalog's own metadata, audit, and lineage tables.
# MAGIC - `samples` - Databricks-provided sample datasets.
# MAGIC - Foreign catalogs, if a Lakehouse Federation connection has been configured to an
# MAGIC   external database.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW CATALOGS;

# COMMAND ----------

display(spark.sql("SHOW CATALOGS"))

# Equivalent using the PySpark Catalog API - returns plain Python objects instead of
# a DataFrame, which is handy when you need to loop over results or write assertions.
for catalog in spark.catalog.listCatalogs():
    print(catalog.name)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create a catalog
# MAGIC
# MAGIC This requires `CREATE CATALOG` permission on the metastore.
# MAGIC
# MAGIC Replace `dev_catalog` with your preferred catalog name if you like - just keep it
# MAGIC consistent with the other notebooks in this folder, which reuse the same name.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog
# MAGIC COMMENT 'Development catalog for Unity Catalog learning';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Bonus: assign a managed storage location per catalog instead of relying on the
# MAGIC -- metastore-level default. Requires a storage credential and external location to
# MAGIC -- already exist (see notebook 04 in this folder).
# MAGIC -- CREATE CATALOG IF NOT EXISTS dev_catalog
# MAGIC -- MANAGED LOCATION 'abfss://dev-catalog@<storage-account>.dfs.core.windows.net/'
# MAGIC -- COMMENT 'Development catalog for Unity Catalog learning';

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
# MAGIC A schema is the second-level namespace inside a catalog. Schema and *database*
# MAGIC are the same thing in Databricks - `CREATE DATABASE` still works, but
# MAGIC `CREATE SCHEMA` is the recommended, modern spelling.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS learning
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
# MAGIC This creates a Unity Catalog **managed** table:
# MAGIC
# MAGIC ```text
# MAGIC dev_catalog.learning.demo_customers
# MAGIC ```
# MAGIC
# MAGIC Managed tables are always Delta Lake, Unity Catalog owns the data files under the
# MAGIC schema's managed storage location, and dropping the table deletes the data files
# MAGIC too - not just the metadata.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE demo_customers (
# MAGIC   customer_id INT,
# MAGIC   customer_name STRING,
# MAGIC   country STRING,
# MAGIC   created_at DATE
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO demo_customers VALUES
# MAGIC   (1, 'Ada Lovelace', 'UK', DATE '2026-01-01'),
# MAGIC   (2, 'Alan Turing', 'UK', DATE '2026-01-02'),
# MAGIC   (3, 'Grace Hopper', 'US', DATE '2026-01-03');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Query with a fully qualified name
# MAGIC
# MAGIC Prefer this form in production code, since it does not depend on the session's
# MAGIC current catalog/schema:
# MAGIC
# MAGIC ```text
# MAGIC catalog.schema.table
# MAGIC ```
# MAGIC
# MAGIC Bonus: Databricks SQL also supports the `IDENTIFIER()` clause, which lets you
# MAGIC build a fully qualified name from a string at runtime - useful when a job
# MAGIC parameter controls which table to read.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM dev_catalog.learning.demo_customers;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- SELECT * FROM IDENTIFIER('dev_catalog.learning.demo_customers');

# COMMAND ----------

# The Python-native equivalent of a fully qualified SELECT.
display(spark.table("dev_catalog.learning.demo_customers"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Inspect table metadata
# MAGIC
# MAGIC `DESCRIBE TABLE EXTENDED` is the quickest way to confirm whether a table is
# MAGIC managed or external: check the `Type` field (`MANAGED` vs `EXTERNAL`) and the
# MAGIC `Location` field (points inside the schema's managed storage for managed tables,
# MAGIC or at your own cloud path for external tables).

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

for table in spark.catalog.listTables("learning"):
    print(table.name, "-", "temporary" if table.isTemporary else "permanent")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Create a view
# MAGIC
# MAGIC Views are also governed Unity Catalog objects: you can grant `SELECT` on a view
# MAGIC without ever granting access to the underlying table, which is the standard way
# MAGIC to expose a restricted or reshaped subset of sensitive data.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW uk_customers AS
# MAGIC SELECT customer_id, customer_name, country
# MAGIC FROM demo_customers
# MAGIC WHERE country = 'UK';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM uk_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Inspect grants
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

def show_grants_safely(securable_type: str, securable_name: str) -> None:
    """Print grants for a Unity Catalog securable without crashing the notebook
    if the caller lacks permission to inspect them."""
    try:
        display(spark.sql(f"SHOW GRANTS ON {securable_type} {securable_name}"))
    except Exception as e:
        print(f"Could not read grants on {securable_type} {securable_name}: {e}")


show_grants_safely("CATALOG", "dev_catalog")
show_grants_safely("SCHEMA", "dev_catalog.learning")
show_grants_safely("TABLE", "dev_catalog.learning.demo_customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Example permission grants
# MAGIC
# MAGIC Do not run these unless you are allowed to manage access.
# MAGIC
# MAGIC Replace `data-users` with a real Databricks group. Grant privileges to **groups**,
# MAGIC not individual users - it is much easier to onboard/offboard people from a group
# MAGIC than to track down every object a person was granted access to directly.

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

# MAGIC %sql
# MAGIC -- Ownership can also be transferred to a group so no single person is a
# MAGIC -- bottleneck (or a single point of failure if their account is disabled):
# MAGIC -- ALTER CATALOG dev_catalog SET OWNER TO `data-engineers`;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Create a managed volume
# MAGIC
# MAGIC Volumes are Unity Catalog objects for governing files. This creates a **managed**
# MAGIC volume - Unity Catalog owns the storage, similar to a managed table. Notebook `04`
# MAGIC in this folder covers **external** volumes, which point at a cloud path you
# MAGIC already own.
# MAGIC
# MAGIC Volume path format:
# MAGIC
# MAGIC ```text
# MAGIC /Volumes/catalog/schema/volume/
# MAGIC ```

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE VOLUME IF NOT EXISTS demo_volume
# MAGIC COMMENT 'Managed volume for Unity Catalog learning';

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW VOLUMES;

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE VOLUME demo_volume;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 15. Write and list files in the volume
# MAGIC
# MAGIC A brand-new volume is empty, so listing it returns nothing until files exist.
# MAGIC Write a sample file first with `dbutils.fs`, then list it.

# COMMAND ----------

volume_path = "/Volumes/dev_catalog/learning/demo_volume"

dbutils.fs.put(f"{volume_path}/hello.txt", "Hello from a Unity Catalog managed volume!\n", overwrite=True)

display(dbutils.fs.ls(volume_path))

# COMMAND ----------

# MAGIC %sql
# MAGIC LIST '/Volumes/dev_catalog/learning/demo_volume/';

# COMMAND ----------

# Volumes are also exposed as a real filesystem path on Unity Catalog-enabled
# compute, so plain Python file I/O works too - no dbutils required.
with open(f"{volume_path}/hello_native.txt", "w") as f:
    f.write("Volumes also work with native Python file I/O.\n")

display(dbutils.fs.ls(volume_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 16. Document objects with comments and tags
# MAGIC
# MAGIC Comments and tags are what keep Catalog Explorer search useful as a catalog
# MAGIC grows - future readers (including you, in six months) shouldn't have to guess
# MAGIC what a table or column means.

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE dev_catalog.learning.demo_customers IS
# MAGIC 'Practice customer dimension for the Unity Catalog learning module';

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE dev_catalog.learning.demo_customers
# MAGIC ALTER COLUMN country COMMENT 'Free-text country label used for practice data only, not validated against ISO codes';

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE dev_catalog.learning.demo_customers
# MAGIC SET TBLPROPERTIES ('data_owner' = 'data-engineering-training', 'pii' = 'false');

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Newer Databricks Runtime versions also support governed, searchable tags
# MAGIC -- (distinct from free-form TBLPROPERTIES) on catalogs, schemas, tables, and
# MAGIC -- columns, if tags are enabled for your metastore:
# MAGIC -- ALTER TABLE dev_catalog.learning.demo_customers SET TAGS ('sensitivity' = 'low');

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE EXTENDED demo_customers;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 17. Use information_schema to explore Unity Catalog metadata
# MAGIC
# MAGIC Unity Catalog metadata can be queried through `system.information_schema` -
# MAGIC handy for building your own data-catalog dashboards or automated audits.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system.information_schema.catalogs;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system.information_schema.schemata
# MAGIC WHERE catalog_name = 'dev_catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system.information_schema.tables
# MAGIC WHERE table_catalog = 'dev_catalog'
# MAGIC   AND table_schema = 'learning';

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM system.information_schema.columns
# MAGIC WHERE table_catalog = 'dev_catalog'
# MAGIC   AND table_schema = 'learning'
# MAGIC   AND table_name = 'demo_customers';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 18. Create a second table for practice

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE demo_orders (
# MAGIC   order_id INT,
# MAGIC   customer_id INT,
# MAGIC   order_amount DECIMAL(10, 2),
# MAGIC   order_date DATE
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO demo_orders VALUES
# MAGIC   (101, 1, 120.50, DATE '2026-02-01'),
# MAGIC   (102, 1, 75.00, DATE '2026-02-02'),
# MAGIC   (103, 2, 210.99, DATE '2026-02-03'),
# MAGIC   (104, 3, 49.90, DATE '2026-02-04'),
# MAGIC   (105, 3, 300.00, DATE '2026-02-05');

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   c.customer_id,
# MAGIC   c.customer_name,
# MAGIC   c.country,
# MAGIC   o.order_id,
# MAGIC   o.order_amount,
# MAGIC   o.order_date
# MAGIC FROM demo_customers c
# MAGIC JOIN demo_orders o
# MAGIC   ON c.customer_id = o.customer_id;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 19. Create a governed summary view

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW order_summary_public AS
# MAGIC SELECT
# MAGIC   c.customer_id,
# MAGIC   c.country,
# MAGIC   COUNT(o.order_id) AS order_count,
# MAGIC   SUM(o.order_amount) AS total_order_amount
# MAGIC FROM demo_customers c
# MAGIC JOIN demo_orders o
# MAGIC   ON c.customer_id = o.customer_id
# MAGIC GROUP BY
# MAGIC   c.customer_id,
# MAGIC   c.country;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM order_summary_public;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 20. Bonus: parameterize catalog and schema names with widgets
# MAGIC
# MAGIC `%sql` cells cannot read Python variables directly, so DDL that must be
# MAGIC parameterized (for example, to run the same notebook against `dev`, `test`, and
# MAGIC `prod` catalogs from a Databricks Job) belongs in a Python cell that builds the
# MAGIC SQL string and runs it with `spark.sql(...)`.

# COMMAND ----------

dbutils.widgets.text("catalog_name", "dev_catalog", "Catalog name")
dbutils.widgets.text("schema_name", "learning", "Schema name")

catalog_name = dbutils.widgets.get("catalog_name")
schema_name = dbutils.widgets.get("schema_name")

print(f"Parameterized target: {catalog_name}.{schema_name}")

# COMMAND ----------

# IF NOT EXISTS makes this safe to rerun. With the default widget values this just
# re-confirms dev_catalog.learning, which was already created earlier in this
# notebook - change the widget values above and rerun to target a different
# catalog/schema without touching any code.
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog_name} COMMENT 'Created via parameterized widget example'")
spark.sql(f"USE CATALOG {catalog_name}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name} COMMENT 'Created via parameterized widget example'")
spark.sql(f"USE SCHEMA {schema_name}")

resolved_catalog = spark.sql("SELECT current_catalog()").collect()[0][0]
resolved_schema = spark.sql("SELECT current_schema()").collect()[0][0]
print(f"Now using {resolved_catalog}.{resolved_schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 21. Lineage and system tables
# MAGIC
# MAGIC Unity Catalog captures table- and column-level lineage automatically for every
# MAGIC read/write it sees, across notebooks, jobs, dashboards, and pipelines - no extra
# MAGIC instrumentation needed. You can inspect it two ways:
# MAGIC
# MAGIC - **Catalog Explorer** - open any table or column and check its **Lineage** tab.
# MAGIC - **SQL** - query the `system.access` lineage tables directly, if system schemas
# MAGIC   are enabled for your metastore (usually a one-time setup by an account/
# MAGIC   metastore admin).

# COMMAND ----------

# MAGIC %sql
# MAGIC -- SELECT * FROM system.access.table_lineage
# MAGIC -- WHERE target_table_full_name = 'dev_catalog.learning.order_summary_public';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 22. Common errors and how to read them
# MAGIC
# MAGIC **`current_metastore()` fails or returns `NULL`**
# MAGIC The workspace is not attached to a Unity Catalog metastore, or the attached
# MAGIC compute's access mode does not support Unity Catalog.
# MAGIC
# MAGIC **`CATALOG_NOT_FOUND` / `SCHEMA_NOT_FOUND`**
# MAGIC Wrong name, missing `USE CATALOG`/`USE SCHEMA` privilege, or you are connected to
# MAGIC a different metastore than you expect.
# MAGIC
# MAGIC **`PERMISSION_DENIED` / insufficient privileges**
# MAGIC Missing `USE CATALOG`, `USE SCHEMA`, `SELECT`, or `CREATE TABLE`/`CREATE SCHEMA`.
# MAGIC Check with `SHOW GRANTS` (Section 12) before assuming the object doesn't exist.
# MAGIC
# MAGIC **`TABLE_OR_VIEW_NOT_FOUND`**
# MAGIC Usually the current catalog/schema is not what you think. Use a fully qualified
# MAGIC name (`catalog.schema.table`) to remove the ambiguity entirely.
# MAGIC
# MAGIC **Permission errors reading/writing a volume path**
# MAGIC Missing `READ VOLUME`/`WRITE VOLUME` privilege on that specific volume, separate
# MAGIC from table privileges.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 23. Best practices checklist
# MAGIC
# MAGIC - Prefer fully qualified `catalog.schema.object` names in production code and
# MAGIC   jobs; rely on `USE CATALOG`/`USE SCHEMA` only for interactive exploration.
# MAGIC - Pick one catalog strategy - per environment (dev/test/prod) or per business
# MAGIC   domain - and stick to it. Consider workspace-catalog bindings so a dev
# MAGIC   workspace cannot reach the prod catalog even on a shared metastore.
# MAGIC - Grant privileges to **groups**, not individual users, and keep metastore admin
# MAGIC   tightly scoped.
# MAGIC - Default to **managed** tables/volumes; only reach for external tables/volumes
# MAGIC   plus storage credentials and external locations when the data is genuinely
# MAGIC   owned by another system.
# MAGIC - Document as you go: `COMMENT ON`, `TBLPROPERTIES`, and tags keep Catalog
# MAGIC   Explorer search useful as the catalog grows.
# MAGIC - Treat cleanup scripts (`DROP ... CASCADE`) with the same care as production
# MAGIC   DDL - review before running, especially against shared catalogs.
# MAGIC - Use system tables and the Lineage tab instead of building your own auditing -
# MAGIC   Unity Catalog already tracks it once system schemas are enabled.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 24. Cleanup
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

# Remove the widgets created in the bonus parameterization section.
# dbutils.widgets.removeAll()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC You learned:
# MAGIC
# MAGIC - what Unity Catalog is and how it differs from the legacy Hive metastore/DBFS
# MAGIC - the full object model: metastore, catalog, schema, table, view, function,
# MAGIC   volume, storage credential, external location, and Delta Sharing objects
# MAGIC - the difference between managed and external tables/volumes
# MAGIC - how to check metastore attachment, in both SQL and Python
# MAGIC - how to create a catalog, a schema, managed tables, and views
# MAGIC - how to inspect and grant permissions, and why grants belong on groups
# MAGIC - how to create a managed volume and read/write files in it
# MAGIC - how to document objects with comments, properties, and tags
# MAGIC - how to query Unity Catalog metadata via `system.information_schema`
# MAGIC - how lineage is captured automatically and where to see it
# MAGIC - how to parameterize catalog/schema names with widgets for reusable notebooks
# MAGIC - common errors and how to diagnose them
# MAGIC - how to clean up practice objects safely
# MAGIC
# MAGIC Core model:
# MAGIC
# MAGIC ```text
# MAGIC metastore -> catalog -> schema -> table/view/function/volume
# MAGIC ```
# MAGIC
# MAGIC Continue in this folder with:
# MAGIC
# MAGIC - `02_uc_setup_concepts.py` - admin-level metastore setup vs user-level catalog setup
# MAGIC - `03_sql_introduction-to-unity-catalog.sql` - the same workflow in pure SQL
# MAGIC - `04_sql_configure-access-to-cloud-storage.sql` - storage credentials, external
# MAGIC   locations, and external tables/volumes over Azure Data Lake Storage
