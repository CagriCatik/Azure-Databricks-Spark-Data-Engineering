-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Set-up the project environment for Formula1 Project (Incremental Load)
-- MAGIC 1. Create External Location databricks-course-ext-dl1-formula1-incr
-- MAGIC 1. Create Catalog formula1_incr
-- MAGIC 1. Create Schemas landing, bronze, silver and gold
-- MAGIC 1. Create Volume Files in the landing schema
-- MAGIC
-- MAGIC This is a one-time, admin-run setup notebook. It provisions the Unity
-- MAGIC Catalog objects every other notebook in this project depends on -
-- MAGIC nothing here is re-run as part of the regular pipeline, and none of it
-- MAGIC is parameterized through `00-common/01.environment-config`, since that
-- MAGIC notebook's constants (`catalog_name`, `bronze_schema`, ...) describe
-- MAGIC objects this notebook is what actually creates.
-- MAGIC
-- MAGIC This is the incremental-load counterpart of
-- MAGIC `project/04_formula1-project/01-setup/01.Setup Project Environment.sql`.
-- MAGIC The structure is identical; only the names differ - `formula1_incr`
-- MAGIC instead of `formula1`, and the `formula1-incr` storage container
-- MAGIC instead of `formula1` - so the two projects' catalogs, schemas, and
-- MAGIC underlying storage never collide, and each can be torn down
-- MAGIC independently of the other.
-- MAGIC
-- MAGIC For the underlying Unity Catalog concepts (storage credential,
-- MAGIC external location, managed vs. external tables/volumes) see
-- MAGIC `project/02_introduction-to-unity-catalog/01_uc_introduction.py` and, in
-- MAGIC particular,
-- MAGIC `project/02_introduction-to-unity-catalog/04_sql_configure-access-to-cloud-storage.sql`.
-- MAGIC This notebook does not repeat that background - it applies it
-- MAGIC directly to this project's own storage layout.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Access Cloud Storage
-- MAGIC
-- MAGIC Sanity check before creating any Unity Catalog object: confirm the
-- MAGIC cluster's cloud identity can already reach the target ADLS Gen2
-- MAGIC container directly. If this listing fails, the storage credential
-- MAGIC referenced below (`databricks-course-sc`) will fail too, since Unity
-- MAGIC Catalog ultimately relies on the same underlying cloud identity.

-- COMMAND ----------

-- MAGIC %fs ls 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/landing'

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create External Location
-- MAGIC
-- MAGIC An **external location** binds a cloud storage path to a Unity
-- MAGIC Catalog **storage credential** (here, `databricks-course-sc` - an
-- MAGIC existing service principal / managed identity registered separately
-- MAGIC by an account admin, not created by this notebook). Unity Catalog
-- MAGIC uses this pair whenever it needs to touch that path on your behalf:
-- MAGIC
-- MAGIC ```text
-- MAGIC Storage Credential (cloud identity)
-- MAGIC   -> External Location (credential + path, e.g. this container root)
-- MAGIC     -> Catalog MANAGED LOCATION (below)
-- MAGIC     -> Schema MANAGED LOCATION (below)
-- MAGIC     -> External Volume (below)
-- MAGIC ```
-- MAGIC
-- MAGIC The URL is the container root (`.../formula1-incr@.../`), so one
-- MAGIC external location covers every managed location and volume created
-- MAGIC under it later in this notebook - each only needs to be a sub-path of
-- MAGIC an already-registered external location, not a separate credential.

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS databricks_course_ext_dl1_formula1_incr
URL 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL `databricks-course-sc`)
COMMENT 'External location for the formula1-incr container';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Catalog formula1_incr
-- MAGIC
-- MAGIC The catalog is given its own `MANAGED LOCATION`, pointed at the same
-- MAGIC container the external location above covers. Every managed table
-- MAGIC created in `formula1_incr` without its own explicit location is
-- MAGIC stored under this path by default, fully owned and lifecycle-managed
-- MAGIC by Unity Catalog - dropping a managed table deletes its data files,
-- MAGIC not just its metadata.

-- COMMAND ----------

SHOW CATALOGS;

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS formula1_incr
   MANAGED LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/'
   COMMENT 'This is the main catalog for the formula1 incremental-load project' ;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Schemas landing, bronze, silver, gold
-- MAGIC
-- MAGIC Each medallion layer gets its own schema, and each of `bronze`,
-- MAGIC `silver`, and `gold` gets its own `MANAGED LOCATION` subfolder rather
-- MAGIC than inheriting the catalog's root location - keeping the three
-- MAGIC layers' storage physically separated on ADLS (`.../bronze`,
-- MAGIC `.../silver`, `.../gold`), so cost, retention, and access policy can
-- MAGIC be reasoned about independently per layer.
-- MAGIC
-- MAGIC `landing` is deliberately the exception: it has **no** `MANAGED
-- MAGIC LOCATION` of its own, because it holds no managed tables - its only
-- MAGIC purpose is to be the parent schema for the `files` **external**
-- MAGIC volume created below, whose location is specified explicitly at the
-- MAGIC volume level instead.
-- MAGIC
-- MAGIC Note there is no `control` schema created here. It is created
-- MAGIC separately by `06-orchestration/00.Create Control Tables.py`, since
-- MAGIC batch-orchestration metadata is a distinct concern from this
-- MAGIC notebook's job of provisioning the medallion data layers.

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS formula1_incr.landing;
CREATE SCHEMA IF NOT EXISTS formula1_incr.bronze
    MANAGED LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/bronze';
CREATE SCHEMA IF NOT EXISTS formula1_incr.silver
    MANAGED LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/silver';
CREATE SCHEMA IF NOT EXISTS formula1_incr.gold
    MANAGED LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/gold';

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

USE CATALOG formula1_incr;

-- COMMAND ----------

SHOW SCHEMAS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Volume Files
-- MAGIC
-- MAGIC `formula1_incr.landing.files` is created as an **EXTERNAL** volume,
-- MAGIC not a managed one - the raw F1 CSV/JSON source files land in this
-- MAGIC path via an external process (a data drop, ADF copy activity, or
-- MAGIC manual upload) that runs outside Databricks and outside Unity
-- MAGIC Catalog's control. An external volume lets Unity Catalog govern
-- MAGIC access to files that already exist (or will be written) at a cloud
-- MAGIC path you own, without claiming ownership of - or deleting - those
-- MAGIC files if the volume is ever dropped.
-- MAGIC
-- MAGIC Unlike the full-refresh project, source files here are not dropped
-- MAGIC directly under this volume's root - each batch lands in its own
-- MAGIC numbered subfolder, e.g. `.../files/1/circuits.csv`,
-- MAGIC `.../files/2/circuits.csv`, and so on. Every bronze ingestion
-- MAGIC notebook in `02-bronze` builds that per-batch path from
-- MAGIC `landing_folder_path` (in `00-common/01.environment-config`) plus the
-- MAGIC `p_batch_id` widget it is called with.

-- COMMAND ----------

CREATE EXTERNAL VOLUME formula1_incr.landing.files
LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/landing';

-- COMMAND ----------

-- MAGIC %fs ls /Volumes/formula1_incr/landing/files
