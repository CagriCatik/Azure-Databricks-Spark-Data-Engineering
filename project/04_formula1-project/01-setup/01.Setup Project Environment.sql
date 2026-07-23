-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Set-up the project environment for Formula1 Project
-- MAGIC 1. Create External Location databricks-course-ext-dl1-formula1
-- MAGIC 1. Create Catalog formula1
-- MAGIC 1. Create Schemas landing, bronze, silver and gold
-- MAGIC 1. Create Volume Files in the landing schema
-- MAGIC
-- MAGIC This is a one-time, admin-run setup notebook. It provisions the Unity
-- MAGIC Catalog objects that every other notebook in this project depends on -
-- MAGIC nothing here is re-run as part of the regular pipeline, and none of it is
-- MAGIC parameterized through `00-common/01.environment-config`, since that
-- MAGIC notebook's constants (`catalog_name`, `bronze_schema`, ...) describe objects
-- MAGIC this notebook is what actually creates.
-- MAGIC
-- MAGIC For the underlying Unity Catalog concepts (storage credential, external
-- MAGIC location, managed vs. external tables/volumes) see
-- MAGIC `project/02_introduction-to-unity-catalog/01_uc_introduction.py` and, in
-- MAGIC particular,
-- MAGIC `project/02_introduction-to-unity-catalog/04_sql_configure-access-to-cloud-storage.sql`,
-- MAGIC which walks through storage credentials and external locations step by
-- MAGIC step. This notebook does not repeat that background - it applies it
-- MAGIC directly to the `formula1` project's own storage layout.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Access Cloud Storage
-- MAGIC
-- MAGIC Sanity check before creating any Unity Catalog object: confirm the
-- MAGIC cluster's cloud identity can already reach the target ADLS Gen2 container
-- MAGIC directly. If this listing fails, the storage credential referenced below
-- MAGIC (`databricks-course-sc`) will fail too, since Unity Catalog ultimately
-- MAGIC relies on the same underlying cloud identity.

-- COMMAND ----------

-- MAGIC %fs ls 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/landing'

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create External Location
-- MAGIC
-- MAGIC An **external location** binds a cloud storage path to a Unity Catalog
-- MAGIC **storage credential** (here, `databricks-course-sc` - an existing
-- MAGIC service principal / managed identity registered separately by an account
-- MAGIC admin, not created by this notebook). Unity Catalog uses this pair
-- MAGIC whenever it needs to touch that path on your behalf:
-- MAGIC
-- MAGIC ```text
-- MAGIC Storage Credential (cloud identity)
-- MAGIC   -> External Location (credential + path, e.g. this container root)
-- MAGIC     -> Catalog MANAGED LOCATION (below)
-- MAGIC     -> Schema MANAGED LOCATION (below)
-- MAGIC     -> External Volume (below)
-- MAGIC ```
-- MAGIC
-- MAGIC The URL is the container root (`.../formula1@.../`), so one external
-- MAGIC location covers every managed location and volume created under it later
-- MAGIC in this notebook - each of those only needs to be a sub-path of an
-- MAGIC already-registered external location, not a separate credential.

-- COMMAND ----------

CREATE EXTERNAL LOCATION IF NOT EXISTS databricks_course_ext_dl1_formula1
URL 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL `databricks-course-sc`)
COMMENT 'External location for the formula1 container';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Catalog formula1
-- MAGIC
-- MAGIC The catalog is given its own `MANAGED LOCATION`, pointed at the same
-- MAGIC container the external location above covers. This means every table
-- MAGIC created in `formula1` without its own explicit location (i.e. every
-- MAGIC managed table) is stored under this path by default, fully owned and
-- MAGIC lifecycle-managed by Unity Catalog - dropping a managed table deletes its
-- MAGIC data files, not just its metadata.
-- MAGIC
-- MAGIC Assigning storage per catalog (and, below, per schema) rather than
-- MAGIC relying on one metastore-wide default location is what makes each layer's
-- MAGIC storage separately scoped, discoverable, and cost-trackable - you can see
-- MAGIC exactly how much data `formula1/bronze` vs. `formula1/gold` occupies just
-- MAGIC by looking at their respective ADLS folders.

-- COMMAND ----------

SHOW CATALOGS;

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS formula1
   MANAGED LOCATION 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/'
   COMMENT 'This is the main catalog for the formula1 project' ;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Schemas landing, bronze, silver, gold
-- MAGIC
-- MAGIC Each medallion layer gets its own schema, and each of `bronze`, `silver`,
-- MAGIC and `gold` gets its own `MANAGED LOCATION` subfolder rather than
-- MAGIC inheriting the catalog's root location. That keeps the three layers'
-- MAGIC storage physically separated on ADLS (`.../bronze`, `.../silver`,
-- MAGIC `.../gold`), which makes it possible to reason about cost, retention, and
-- MAGIC access policy independently per layer - for example, granting broad read
-- MAGIC access to `gold` for BI consumers while keeping `bronze`/`silver` locked
-- MAGIC down to the engineering team.
-- MAGIC
-- MAGIC `landing` is deliberately the exception: it has **no** `MANAGED LOCATION`
-- MAGIC of its own, because it holds no managed tables - its only purpose is to
-- MAGIC be the parent schema for the `files` **external** volume created below,
-- MAGIC whose location is specified explicitly at the volume level instead.

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS formula1.landing;
CREATE SCHEMA IF NOT EXISTS formula1.bronze
    MANAGED LOCATION 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/bronze';
CREATE SCHEMA IF NOT EXISTS formula1.silver
    MANAGED LOCATION 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/silver';
CREATE SCHEMA IF NOT EXISTS formula1.gold
    MANAGED LOCATION 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/gold';

-- COMMAND ----------

SELECT current_catalog();

-- COMMAND ----------

USE CATALOG formula1;

-- COMMAND ----------

SHOW SCHEMAS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ### Create Volume Files
-- MAGIC
-- MAGIC `formula1.landing.files` is created as an **EXTERNAL** volume, not a
-- MAGIC managed one - a deliberate choice, because the raw F1 CSV/JSON source
-- MAGIC files land in this path via an external process (e.g. a data drop, ADF
-- MAGIC copy activity, or manual upload) that runs outside Databricks and outside
-- MAGIC Unity Catalog's control. An external volume lets Unity Catalog govern
-- MAGIC access to files that already exist (or will be written) at a cloud path
-- MAGIC you own, without Unity Catalog claiming ownership of - or deleting - those
-- MAGIC files if the volume is ever dropped. A managed volume would be the wrong
-- MAGIC choice here: dropping it would delete the landing files along with it,
-- MAGIC and Unity Catalog would expect to be the sole writer.
-- MAGIC
-- MAGIC Every bronze ingestion notebook in `02-bronze` reads its source file from
-- MAGIC this exact volume, via `landing_folder_path` in
-- MAGIC `00-common/01.environment-config`.

-- COMMAND ----------

CREATE EXTERNAL VOLUME formula1.landing.files
LOCATION 'abfss://formula1@databrickscourseextdl1.dfs.core.windows.net/landing';

-- COMMAND ----------

-- MAGIC %fs ls /Volumes/formula1/landing/files
