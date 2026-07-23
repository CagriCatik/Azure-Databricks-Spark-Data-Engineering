# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Setup Concepts: Admin vs. User
# MAGIC
# MAGIC `01_uc_introduction.py` in this same folder covers the full Unity Catalog
# MAGIC object model and a user-level hands-on walkthrough - read that one first if
# MAGIC you haven't. This notebook zooms in on a single question that trips up almost
# MAGIC everyone new to Unity Catalog:
# MAGIC
# MAGIC > "How do I create Unity Catalog?"
# MAGIC
# MAGIC That question conflates two very different operations:
# MAGIC
# MAGIC 1. **Create or enable the Unity Catalog metastore** - a one-time,
# MAGIC    **account-admin** task performed in the Account Console, outside of any
# MAGIC    notebook. This is "turning Unity Catalog on" for a cloud region.
# MAGIC 2. **Create a catalog inside Unity Catalog** - an everyday, **user-level** SQL
# MAGIC    operation (`CREATE CATALOG ...`), run by anyone with the right privilege,
# MAGIC    once a workspace is already attached to a metastore.
# MAGIC
# MAGIC This notebook draws that boundary precisely: Account Console navigation, the
# MAGIC metastore admin role, workspace-catalog bindings, and a concrete comparison of
# MAGIC what each side can and cannot do. For the full object model (schema, table,
# MAGIC view, function, volume, storage credential, ...) and managed-vs-external
# MAGIC tables, see `01_uc_introduction.py`.
# MAGIC
# MAGIC Object hierarchy, for reference:
# MAGIC
# MAGIC ```text
# MAGIC Metastore     (one per cloud region, account-level - Section 2 below)
# MAGIC   Catalog     (Section 6 below)
# MAGIC     Schema
# MAGIC       Table
# MAGIC       View
# MAGIC       Volume
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Check whether Unity Catalog is already enabled
# MAGIC
# MAGIC If this returns a value, the workspace is attached to a Unity Catalog
# MAGIC metastore. If it returns `NULL` or fails, either the workspace is not attached
# MAGIC to one, or the attached compute's access mode does not support Unity Catalog.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_metastore();

# COMMAND ----------

# Unlike a metastore, a workspace is trivial to identify from inside a notebook.
# Printing both together makes the "one metastore, many workspaces" relationship
# concrete - the same metastore ID below may be shared by several other
# workspaces in the same cloud region.
try:
    metastore_id = spark.sql("SELECT current_metastore() AS id").collect()[0]["id"]
except Exception as e:
    metastore_id = None
    print(f"This workspace does not appear to be attached to a Unity Catalog metastore: {e}")

workspace_url = spark.conf.get("spark.databricks.workspaceUrl", "unknown")

if metastore_id:
    print(f"Workspace '{workspace_url}' is attached to metastore '{metastore_id}'.")
    print("Note: that metastore may also be attached to several other workspaces in the same region.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Admin-level setup: enabling the metastore in the Account Console
# MAGIC
# MAGIC This is normally a one-time task for an **account admin**, done entirely
# MAGIC outside of a notebook:
# MAGIC
# MAGIC 1. Sign in to the Databricks Account Console
# MAGIC    (`accounts.azuredatabricks.net` on Azure) as an account admin.
# MAGIC 2. Go to **Catalog** -> **Create metastore**.
# MAGIC 3. Name the metastore and pick a cloud region - it must match the region of
# MAGIC    the workspaces you plan to attach, and Databricks allows only **one
# MAGIC    metastore per region**.
# MAGIC 4. Optionally set a default managed storage location for the metastore. Most
# MAGIC    teams leave this blank and instead assign managed storage **per catalog or
# MAGIC    schema**, so cost and access can be scoped per business area instead of
# MAGIC    pooled into one container. See `04_sql_configure-access-to-cloud-storage.sql`
# MAGIC    for the Azure storage-credential mechanics behind this.
# MAGIC 5. On the metastore's **Workspaces** tab, assign the workspace(s) that should
# MAGIC    attach to it. A workspace can be attached to only **one** metastore at a
# MAGIC    time.
# MAGIC 6. Set the **metastore admin** (Section 3 below) - ideally a group.
# MAGIC 7. Back in a notebook attached to that workspace, confirm with
# MAGIC    `SELECT current_metastore();` (Section 1 above).
# MAGIC
# MAGIC If your Azure subscription was created after November 2023, steps 1-6 already
# MAGIC happened automatically the first time a workspace was deployed in that
# MAGIC region - most learners only ever do step 7.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. The metastore admin role
# MAGIC
# MAGIC Every metastore has exactly one admin, set when the metastore is created and
# MAGIC changeable later from the Account Console or Catalog Explorer. Databricks
# MAGIC strongly recommends assigning a **group** rather than an individual user - if
# MAGIC the one person holding the role leaves or is deactivated, nobody is locked
# MAGIC out of managing the metastore.
# MAGIC
# MAGIC The metastore admin is effectively the superuser for that metastore's data
# MAGIC governance. By default they can:
# MAGIC
# MAGIC - Create catalogs, external locations, storage credentials, shares, and
# MAGIC   recipients - the metastore-level `CREATE ...` privileges are implicit for
# MAGIC   this role, not something a regular user gets for free.
# MAGIC - Grant, revoke, or transfer ownership of **any** securable in the metastore,
# MAGIC   even objects they did not create and do not own - useful for offboarding an
# MAGIC   employee who owned catalogs nobody else has access to.
# MAGIC - View and manage every catalog's workspace bindings (Section 4).
# MAGIC
# MAGIC This is a distinct role from two others it is easy to conflate it with:
# MAGIC
# MAGIC - **Account admin** manages the account as a whole: billing, workspaces,
# MAGIC   account-level identities, and which metastore is assigned to which
# MAGIC   workspace. An account admin is not automatically a metastore admin on every
# MAGIC   metastore in the account - the roles are assigned independently, even
# MAGIC   though the same group often holds both in a small organization.
# MAGIC - **Workspace admin** manages workspace-local settings only - cluster
# MAGIC   policies, workspace-level access control, job permissions. Being a
# MAGIC   workspace admin grants **no** Unity Catalog privilege by itself; Unity
# MAGIC   Catalog privileges live at the metastore/catalog/schema/object level, not
# MAGIC   the workspace level.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Workspace-catalog bindings
# MAGIC
# MAGIC By default, once a catalog exists, **every** workspace attached to the same
# MAGIC metastore can see and use it (subject to the usual `USE CATALOG`/`USE SCHEMA`/
# MAGIC `SELECT` grants). That is often too permissive: many organizations run one
# MAGIC shared metastore per region but keep separate `dev`, `test`, and `prod`
# MAGIC workspaces, and do not want a notebook running in the dev workspace to be
# MAGIC able to even *see* the prod catalog.
# MAGIC
# MAGIC **Workspace-catalog bindings** solve this without requiring a metastore per
# MAGIC environment: a metastore admin (or a catalog owner) can restrict a catalog -
# MAGIC or a storage credential, or an external location - to only specific
# MAGIC workspaces bound to the shared metastore.
# MAGIC
# MAGIC Where this is configured:
# MAGIC
# MAGIC - Catalog Explorer -> select the catalog -> **Workspaces** tab -> switch from
# MAGIC   "All workspaces have access" to "Assign to specific workspaces".
# MAGIC - The Account Console, on the metastore's catalog list.
# MAGIC - The Databricks CLI/SDK (workspace-binding APIs), for automated setup as part
# MAGIC   of infrastructure-as-code.
# MAGIC
# MAGIC Important distinction: a workspace binding controls **visibility** - whether
# MAGIC a workspace can reach the catalog at all - not fine-grained access. A user in
# MAGIC a bound workspace still needs the normal `GRANT`s on top to actually read or
# MAGIC write anything inside it.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Account admin vs. metastore admin vs. workspace user
# MAGIC
# MAGIC | Action | Account admin | Metastore admin | Regular workspace user |
# MAGIC | --- | --- | --- | --- |
# MAGIC | Create or delete a metastore | Yes | No | No |
# MAGIC | Assign or remove a workspace on a metastore | Yes | No | No |
# MAGIC | Set or replace the metastore admin | Yes | No | No |
# MAGIC | Manage account-level users, groups, service principals (SCIM) | Yes | No | No |
# MAGIC | Configure workspace-catalog bindings | Yes, via Account Console | Yes, via Catalog Explorer/API | No |
# MAGIC | `CREATE CATALOG` by default, with no explicit grant | Only if also metastore admin | Yes | No |
# MAGIC | Grant/revoke privileges on any securable, even ones they don't own | Only if also metastore admin | Yes | No - only on objects they own or were given `MANAGE`/ownership |
# MAGIC | Create catalogs/schemas/tables/views/volumes once granted the privilege | Yes | Yes | Yes |
# MAGIC
# MAGIC Mental model to keep in your back pocket:
# MAGIC
# MAGIC ```text
# MAGIC Account admin enables Unity Catalog by creating and assigning a metastore.
# MAGIC Metastore admin governs everything inside that metastore day to day.
# MAGIC Everyone else creates catalogs, schemas, tables, views, and volumes inside it -
# MAGIC   once granted the privilege to do so.
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. User-level setup: create a catalog
# MAGIC
# MAGIC Once the workspace is attached to a metastore, anyone with `CREATE CATALOG`
# MAGIC can create a catalog - the first-level namespace in:
# MAGIC
# MAGIC ```text
# MAGIC catalog.schema.table
# MAGIC ```
# MAGIC
# MAGIC This walkthrough builds `dev_catalog.learning.customers`, reusing the same
# MAGIC catalog and schema as the other notebooks in this folder.

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %md
# MAGIC This may fail if you do not have `CREATE CATALOG` or equivalent
# MAGIC metastore-level privilege.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS dev_catalog
# MAGIC COMMENT 'Development catalog for learning Unity Catalog';

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG dev_catalog;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT current_catalog();

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Create a schema inside the catalog
# MAGIC
# MAGIC A schema is the second-level namespace inside a catalog. Tables, views,
# MAGIC functions, models, and volumes are all created inside a schema.

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
# MAGIC ## 8. Create a table inside Unity Catalog
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
# MAGIC ## 9. Quick reference: the full flow in one block
# MAGIC
# MAGIC Everything from Section 6 onward, as a single copy-pasteable script - handy
# MAGIC once you understand each step and just want the recipe:
# MAGIC
# MAGIC ```sql
# MAGIC SELECT current_metastore();
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
# MAGIC SELECT * FROM customers;
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Bonus: inspect schemas and tables with the Python Catalog API
# MAGIC
# MAGIC This notebook has been 100% SQL so far. Since this is a Python-source
# MAGIC notebook, `spark.catalog` is the native way to do the same inspection from
# MAGIC Python instead of parsing `SHOW SCHEMAS`/`SHOW TABLES` output - useful when a
# MAGIC job needs to loop over catalog metadata programmatically.

# COMMAND ----------

spark.catalog.setCurrentCatalog("dev_catalog")

for db in spark.catalog.listDatabases():
    print(db.name, "-", db.description)

# COMMAND ----------

for table in spark.catalog.listTables("learning"):
    print(table.name, "-", "temporary" if table.isTemporary else "permanent")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Required privileges: the privilege chain
# MAGIC
# MAGIC To create and query Unity Catalog objects, a privilege is required at every
# MAGIC level you touch - holding `SELECT` on a table does not help if you are also
# MAGIC missing `USE CATALOG` on its catalog or `USE SCHEMA` on its schema.
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
# MAGIC The common read-access pattern is the three privileges you need together,
# MAGIC bottom-up:
# MAGIC
# MAGIC ```text
# MAGIC USE CATALOG on the catalog
# MAGIC USE SCHEMA on the schema
# MAGIC SELECT on the table or view
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Example grants
# MAGIC
# MAGIC Do not run these unless you are allowed to manage permissions. Replace
# MAGIC `data-users` with a real Databricks group - grant privileges to **groups**,
# MAGIC not individual users.

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
# MAGIC ## 13. Inspect grants
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
# MAGIC ## 14. Cleanup
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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC You learned:
# MAGIC
# MAGIC - the two meanings hiding behind "create Unity Catalog" - enabling a metastore
# MAGIC   (admin) versus creating a catalog (user)
# MAGIC - the Account Console steps an account admin takes to create and assign a
# MAGIC   metastore
# MAGIC - what the metastore admin role is, and how it differs from account admin and
# MAGIC   workspace admin
# MAGIC - what workspace-catalog bindings are and why they let one shared metastore
# MAGIC   safely serve dev/test/prod workspaces
# MAGIC - a concrete comparison of what an account admin, a metastore admin, and a
# MAGIC   regular workspace user can each do
# MAGIC - how to create a catalog, schema, and table as a user, in both SQL and the
# MAGIC   Python Catalog API
# MAGIC - the privilege chain required to read or write a Unity Catalog object
# MAGIC
# MAGIC Continue in this folder with:
# MAGIC
# MAGIC - `01_uc_introduction.py` - the full object model and a deeper user-level
# MAGIC   walkthrough
# MAGIC - `03_sql_introduction-to-unity-catalog.sql` - the same user-level workflow in
# MAGIC   pure SQL, plus functions, comments/tags, and Delta Sharing
# MAGIC - `04_sql_configure-access-to-cloud-storage.sql` - storage credentials,
# MAGIC   external locations, and external tables/volumes over Azure Data Lake Storage
