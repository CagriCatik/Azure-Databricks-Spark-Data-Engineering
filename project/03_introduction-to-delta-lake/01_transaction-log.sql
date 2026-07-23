-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Understanding the Delta Lake Transaction Log
-- MAGIC
-- MAGIC Every Delta table on cloud storage is really two things living side by side in the
-- MAGIC same directory: the **Parquet data files** holding the actual rows, and a
-- MAGIC **`_delta_log`** folder recording every change ever made to the table. The log -
-- MAGIC not the Parquet files by themselves - is the source of truth for what is "in" the
-- MAGIC table at any given version. It is what turns a folder of Parquet files into a
-- MAGIC transactional, versioned, time-travelable **Delta table**.
-- MAGIC
-- MAGIC This notebook:
-- MAGIC
-- MAGIC 1. Creates a dedicated `demo` catalog and `delta_lake` schema backed by Azure Data
-- MAGIC    Lake Storage Gen2 (ADLS Gen2), so the storage layout is easy to reason about.
-- MAGIC 2. Creates a `companies` Delta table and writes to it a couple of times.
-- MAGIC 3. Inspects the table's actual storage location and walks through what you would
-- MAGIC    find inside it - a `_delta_log/` folder of JSON commit files (plus a
-- MAGIC    checkpoint Parquet file every 10 commits, once a table has enough history)
-- MAGIC    alongside the Parquet data files themselves.
-- MAGIC
-- MAGIC The next notebook, `02_history-and-time-travel.sql`, continues against this exact
-- MAGIC `demo.delta_lake.companies` table to cover `DESCRIBE HISTORY`, time travel, and
-- MAGIC `RESTORE TABLE` - leave the objects created here in place.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Create the demo catalog and schema
-- MAGIC
-- MAGIC `MANAGED LOCATION` points the catalog and schema at a specific ADLS Gen2 path
-- MAGIC instead of the metastore's default managed storage - useful here so we know
-- MAGIC exactly which storage account and container to reason about later in this
-- MAGIC notebook.
-- MAGIC
-- MAGIC `abfss://<container>@<storage-account>.dfs.core.windows.net/...` is the **ABFS**
-- MAGIC (Azure Blob Filesystem) driver URI scheme Databricks uses to address ADLS Gen2.
-- MAGIC Creating a catalog or schema with `MANAGED LOCATION` requires:
-- MAGIC
-- MAGIC - `CREATE CATALOG` (or `CREATE SCHEMA`) privilege on the metastore/catalog.
-- MAGIC - An **external location** already registered over that path, backed by a
-- MAGIC   **storage credential** (managed identity or service principal) with write
-- MAGIC   access - both are one-time admin setup, not something this notebook does.
-- MAGIC
-- MAGIC Both statements use `IF NOT EXISTS`, so rerunning this notebook is safe.

-- COMMAND ----------

-- MAGIC %python
-- MAGIC
-- MAGIC from datetime import datetime
-- MAGIC import traceback
-- MAGIC
-- MAGIC queries = [
-- MAGIC     ("CURRENT USER", "SELECT current_user() AS current_user"),
-- MAGIC     ("STORAGE CREDENTIALS", "SHOW STORAGE CREDENTIALS"),
-- MAGIC     ("EXTERNAL LOCATIONS", "SHOW EXTERNAL LOCATIONS"),
-- MAGIC     (
-- MAGIC         "EXTERNAL LOCATION DETAILS",
-- MAGIC         "DESCRIBE EXTERNAL LOCATION databricks_course"
-- MAGIC     ),
-- MAGIC     (
-- MAGIC         "EXTERNAL LOCATION GRANTS",
-- MAGIC         "SHOW GRANTS ON EXTERNAL LOCATION databricks_course"
-- MAGIC     ),
-- MAGIC ]
-- MAGIC
-- MAGIC print("=" * 120)
-- MAGIC print("UNITY CATALOG STORAGE DIAGNOSTICS")
-- MAGIC print(f"Executed at: {datetime.now()}")
-- MAGIC print("=" * 120)
-- MAGIC
-- MAGIC for title, sql_query in queries:
-- MAGIC     print(f"\n{'=' * 120}")
-- MAGIC     print(title)
-- MAGIC     print("-" * 120)
-- MAGIC     print(f"SQL: {sql_query};")
-- MAGIC     print("-" * 120)
-- MAGIC
-- MAGIC     try:
-- MAGIC         df = spark.sql(sql_query)
-- MAGIC
-- MAGIC         print("Schema:")
-- MAGIC         for field in df.schema.fields:
-- MAGIC             print(f"  - {field.name}: {field.dataType.simpleString()}")
-- MAGIC
-- MAGIC         rows = df.collect()
-- MAGIC
-- MAGIC         print(f"\nNumber of rows: {len(rows)}")
-- MAGIC
-- MAGIC         if not rows:
-- MAGIC             print("  <NO ROWS RETURNED>")
-- MAGIC         else:
-- MAGIC             for row_number, row in enumerate(rows, start=1):
-- MAGIC                 print(f"\nRow {row_number}:")
-- MAGIC                 row_dict = row.asDict(recursive=True)
-- MAGIC
-- MAGIC                 for column, value in row_dict.items():
-- MAGIC                     print(f"  {column}: {value}")
-- MAGIC
-- MAGIC         print(f"\nSTATUS: SUCCESS — {title}")
-- MAGIC
-- MAGIC     except Exception as error:
-- MAGIC         print(f"\nSTATUS: FAILED — {title}")
-- MAGIC         print(f"ERROR TYPE: {type(error).__name__}")
-- MAGIC         print(f"ERROR MESSAGE: {error}")
-- MAGIC         traceback.print_exc(limit=5)
-- MAGIC
-- MAGIC print(f"\n{'=' * 120}")
-- MAGIC print("DIAGNOSTICS COMPLETED")
-- MAGIC print("=" * 120)

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS demo
MANAGED LOCATION 'abfss://demo@databrickscourseextdl1.dfs.core.windows.net/';

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS demo
MANAGED LOCATION
'abfss://unity-catalog-storage@dbstorage53ch6unudau4i.dfs.core.windows.net/7405613508502640/demo_catalog';

CREATE SCHEMA IF NOT EXISTS demo.delta_lake;

USE CATALOG demo;
USE SCHEMA delta_lake;

DESCRIBE CATALOG EXTENDED demo;
DESCRIBE SCHEMA EXTENDED demo.delta_lake;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Create a Delta table
-- MAGIC
-- MAGIC Delta is the **default** table format on Databricks, so `USING DELTA` below is
-- MAGIC optional - it is written explicitly for clarity. Creating the table with no rows
-- MAGIC still produces a transaction log entry: version `0`, operation `CREATE TABLE`,
-- MAGIC with zero Parquet data files referenced (there is nothing to add yet).

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS demo.delta_lake.companies
(
  company_name STRING,
  founded_date DATE,
  country      STRING
)
USING DELTA;

-- COMMAND ----------

DESCRIBE EXTENDED demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC `DESCRIBE EXTENDED` (`DESC EXTENDED` is the same command) confirms `Type` =
-- MAGIC `MANAGED`, and further down under **Detailed Table Information** a `Location`
-- MAGIC field pointing somewhere under the schema's managed path - nested one level
-- MAGIC deeper than you might expect, because Unity Catalog assigns every schema and
-- MAGIC table its own GUID:
-- MAGIC
-- MAGIC ```text
-- MAGIC abfss://demo@databrickscourseextdl1.dfs.core.windows.net/delta_lake/__unitystorage/schemas/<schema-guid>/tables/<table-guid>/
-- MAGIC ```
-- MAGIC
-- MAGIC That directory *is* the table: a `_delta_log/` subfolder plus, once rows are
-- MAGIC written, one or more Parquet data files sitting alongside it.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Inspect the table's storage layout
-- MAGIC
-- MAGIC `DESCRIBE EXTENDED` tells you *where* the table lives; `DESCRIBE DETAIL` tells you
-- MAGIC more about *what's there right now* - size in bytes, file count, format, creation
-- MAGIC time - without needing any direct storage-browsing permission. Prefer
-- MAGIC `DESCRIBE DETAIL` and `DESCRIBE HISTORY` (next notebook) as your primary tools for
-- MAGIC understanding a Delta table's state: both are answered entirely from Unity
-- MAGIC Catalog metadata and the transaction log, using only the table privileges you
-- MAGIC already have.

-- COMMAND ----------

DESCRIBE DETAIL demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC `numFiles` should read `0` right now - the table has no rows yet, so there are no
-- MAGIC Parquet data files, even though the `_delta_log` folder already exists with its
-- MAGIC version-0 commit.
-- MAGIC
-- MAGIC #### Bonus: browsing the raw directory, if you have direct storage access
-- MAGIC
-- MAGIC Unity Catalog privileges (`SELECT`, `USE CATALOG`, ...) are enough for everything
-- MAGIC above, and are deliberately **not** the same thing as direct ADLS Gen2 access (an
-- MAGIC RBAC role or ACL on the storage account itself). Most Unity Catalog users -
-- MAGIC correctly - won't have that. If your account happens to have direct storage
-- MAGIC access, the cell below fetches the table's location from `DESCRIBE DETAIL`
-- MAGIC programmatically and lists it, failing gracefully if that access isn't there:

-- COMMAND ----------

-- MAGIC %python
-- MAGIC location = spark.sql("DESCRIBE DETAIL demo.delta_lake.companies").collect()[0]["location"]
-- MAGIC print(f"Table location: {location}")
-- MAGIC
-- MAGIC try:
-- MAGIC     display(dbutils.fs.ls(location))
-- MAGIC except Exception as e:
-- MAGIC     print(
-- MAGIC         "Could not list the storage path directly - this is expected if you only "
-- MAGIC         "have Unity Catalog access to the table and not direct ADLS RBAC on the "
-- MAGIC         f"underlying storage account. Details: {e}"
-- MAGIC     )

-- COMMAND ----------

-- MAGIC %md
-- MAGIC If that listing succeeded, you'd see a single `_delta_log` folder and no data
-- MAGIC files yet. Listing `_delta_log` itself (`dbutils.fs.ls(location + "/_delta_log")`)
-- MAGIC would show exactly one file: `00000000000000000000.json` - version `0`, the
-- MAGIC `CREATE TABLE` commit.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Insert a row and watch the log grow

-- COMMAND ----------

INSERT INTO demo.delta_lake.companies
VALUES ('Apple', '1976-04-01', 'USA');

-- COMMAND ----------

SELECT * FROM demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC That single `INSERT` is version `1`. Behind the scenes it:
-- MAGIC
-- MAGIC 1. Wrote one new Parquet file containing the Apple row.
-- MAGIC 2. Wrote `_delta_log/00000000000000000001.json`, recording an **`add`** action for
-- MAGIC    that new file plus operation metadata (`WRITE`, row count, and so on).
-- MAGIC
-- MAGIC The table's current state is never simply "whatever Parquet files sit in the
-- MAGIC folder" - it is always "whatever the latest committed log entry says is currently
-- MAGIC active". That distinction is exactly what makes time travel possible: point a
-- MAGIC reader at an earlier log entry, and it reconstructs an earlier - but equally
-- MAGIC valid - table state, covered in the next notebook.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Insert more data

-- COMMAND ----------

INSERT INTO demo.delta_lake.companies
VALUES
  ('Microsoft', '1975-04-04', 'USA'),
  ('Google',  '1998-09-04', 'USA'),
  ('Amazon',  '1994-07-05', 'USA');

-- COMMAND ----------

SELECT * FROM demo.delta_lake.companies;

-- COMMAND ----------

DESCRIBE DETAIL demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC This second `INSERT` is version `2`: another new Parquet file (or files, depending
-- MAGIC on shuffle parallelism) plus `_delta_log/00000000000000000002.json` recording
-- MAGIC `add` actions for whatever was written. `DESCRIBE DETAIL` now reports `numFiles`
-- MAGIC greater than `0` and a non-zero `sizeInBytes`, confirming Parquet data now exists
-- MAGIC on disk. Nothing already committed was rewritten - each write is purely additive
-- MAGIC at the storage level; only the log's bookkeeping of what is currently active
-- MAGIC changes.
-- MAGIC
-- MAGIC With three commits behind it, the table directory now looks like this:
-- MAGIC
-- MAGIC ```text
-- MAGIC <table-guid>/
-- MAGIC ├── _delta_log/
-- MAGIC │   ├── 00000000000000000000.json   version 0 - CREATE TABLE, no files added
-- MAGIC │   ├── 00000000000000000001.json   version 1 - WRITE, adds 1 Parquet file
-- MAGIC │   └── 00000000000000000002.json   version 2 - WRITE, adds more Parquet file(s)
-- MAGIC ├── part-00000-<guid>.snappy.parquet   (Apple)
-- MAGIC └── part-00000-<guid>.snappy.parquet   (Microsoft / Google / Amazon)
-- MAGIC ```
-- MAGIC
-- MAGIC Each JSON commit is a small, append-only ledger entry - later commits never
-- MAGIC rewrite earlier ones. To avoid readers having to replay potentially thousands of
-- MAGIC tiny JSON files to reconstruct current state on a long-lived table, Delta also
-- MAGIC writes a **checkpoint**: a single Parquet file summarizing the entire log up to
-- MAGIC that point, written every **10 commits** by default (the
-- MAGIC `delta.checkpointInterval` table property). Readers then only need the latest
-- MAGIC checkpoint plus whatever JSON commits came after it, not the full history back to
-- MAGIC version 0. This demo only has three commits, so no checkpoint exists yet.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. How the transaction log delivers ACID
-- MAGIC
-- MAGIC The commit behavior you just watched is exactly what makes Delta Lake
-- MAGIC transactional:
-- MAGIC
-- MAGIC - **Atomicity** - each commit is one new file, written completely or not at all.
-- MAGIC   Delta claims the next version number using the storage layer's atomic
-- MAGIC   put-if-absent semantics, so two writers can never both "win" version `3`; a
-- MAGIC   reader never sees a half-written commit.
-- MAGIC - **Consistency** - every write is checked against the table's schema before it
-- MAGIC   is allowed to commit, so the table can never drift into a shape its schema
-- MAGIC   doesn't describe.
-- MAGIC - **Isolation** - concurrent writers use **optimistic concurrency control**: each
-- MAGIC   one reads the current version, prepares its change, then tries to commit the
-- MAGIC   *next* version. If someone else already claimed that version number, the
-- MAGIC   loser's commit is rejected and Delta retries it against the new latest version
-- MAGIC   instead of corrupting anything.
-- MAGIC - **Durability** - once a commit's JSON file exists in `_delta_log`, it is
-- MAGIC   durable (backed by ADLS Gen2's own storage durability), and every reader from
-- MAGIC   that point on will see it.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Why this matters in production
-- MAGIC
-- MAGIC Treating the log - not the files - as the source of truth explains behavior
-- MAGIC you'll rely on later: why `VACUUM` is dangerous if run too aggressively (it
-- MAGIC deletes Parquet files no longer referenced by the retained history, which can
-- MAGIC break time travel - more on this in the next notebook); why concurrent writers
-- MAGIC don't corrupt a table (the log's commit is atomic, and conflicts are resolved with
-- MAGIC optimistic concurrency control rather than locks); and why `DESCRIBE HISTORY`
-- MAGIC gives you a full audit trail for free - every commit, who ran it, and what
-- MAGIC changed - with no extra logging code of your own.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary
-- MAGIC
-- MAGIC - A Delta table is Parquet data files **plus** a `_delta_log` folder of JSON
-- MAGIC   commit files - the log, not the files, is the authoritative record of what's in
-- MAGIC   the table at any version.
-- MAGIC - Each write adds new Parquet file(s) and exactly one new JSON commit recording
-- MAGIC   `add` (and, for updates/deletes, `remove`) actions - it never rewrites prior
-- MAGIC   commits.
-- MAGIC - A checkpoint Parquet file is written every 10 commits by default, so readers
-- MAGIC   don't need to replay the entire history to determine current state.
-- MAGIC - `DESCRIBE EXTENDED` and `DESCRIBE DETAIL` are the right first tools for
-- MAGIC   inspecting a table's location and storage footprint - no direct cloud storage
-- MAGIC   access required.
-- MAGIC
-- MAGIC Continue to `02_history-and-time-travel.sql` to query this table's history, time
-- MAGIC travel across its versions, and restore it to an earlier one.
