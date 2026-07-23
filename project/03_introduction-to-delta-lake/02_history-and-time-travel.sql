-- Databricks notebook source
-- MAGIC %md
-- MAGIC # History and Time Travel
-- MAGIC
-- MAGIC This notebook continues directly from `01_transaction-log.sql` and reuses the same
-- MAGIC `demo.delta_lake.companies` table - run that notebook first if you haven't, since
-- MAGIC this one depends on its three existing commits (`CREATE TABLE`, then two
-- MAGIC `INSERT`s).
-- MAGIC
-- MAGIC Here we:
-- MAGIC
-- MAGIC 1. Query the table's full commit history with `DESCRIBE HISTORY`.
-- MAGIC 2. Time travel to a previous version with `VERSION AS OF`.
-- MAGIC 3. Time travel to a previous point in time with `TIMESTAMP AS OF` - and build a
-- MAGIC    real, valid timestamp for your own run instead of a fixed literal.
-- MAGIC 4. Restore the table to an earlier version with `RESTORE TABLE`, and confirm that
-- MAGIC    restoring **adds** history rather than erasing it.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Query the table's full history
-- MAGIC
-- MAGIC `DESCRIBE HISTORY` reads the `_delta_log` commit metadata directly - it is not a
-- MAGIC separate audit system, just a friendlier view onto the same JSON files this
-- MAGIC table's writes have been producing all along. For each version it reports the
-- MAGIC **version number**, **timestamp**, **user**, **operation** (`CREATE TABLE`,
-- MAGIC `WRITE`, `RESTORE`, ...), and operation metrics (rows written, files
-- MAGIC added/removed, and so on).

-- COMMAND ----------

DESCRIBE HISTORY demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC You should see three rows, newest first:
-- MAGIC
-- MAGIC | Version | Operation |
-- MAGIC | --- | --- |
-- MAGIC | 2 | WRITE (Microsoft, Google, Amazon) |
-- MAGIC | 1 | WRITE (Apple) |
-- MAGIC | 0 | CREATE TABLE |

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Time travel by version
-- MAGIC
-- MAGIC `VERSION AS OF` doesn't read a snapshot copy of the data - it re-derives the table
-- MAGIC state by replaying the log's `add`/`remove` actions up through the requested
-- MAGIC version and ignoring every commit after it. No data is copied or recomputed,
-- MAGIC which is why time travel queries are cheap regardless of how much history a table
-- MAGIC has.

-- COMMAND ----------

-- Latest version - all four rows.
SELECT * FROM demo.delta_lake.companies;

-- COMMAND ----------

-- Table state as of version 1 - only the Apple row existed yet.
SELECT * FROM demo.delta_lake.companies
VERSION AS OF 1;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Time travel by timestamp
-- MAGIC
-- MAGIC `TIMESTAMP AS OF` does the same reconstruction, but you give it a point in time
-- MAGIC instead of a version number - Delta resolves it to "the latest version committed
-- MAGIC at or before that timestamp".

-- COMMAND ----------

-- MAGIC %md
-- MAGIC !!! This exact timestamp is illustrative only
-- MAGIC
-- MAGIC A query like the one below appears in some Delta Lake tutorials with a fixed
-- MAGIC timestamp literal:
-- MAGIC
-- MAGIC ```sql
-- MAGIC SELECT * FROM demo.delta_lake.companies
-- MAGIC TIMESTAMP AS OF '2025-01-07T11:45:12.000+00:00';
-- MAGIC ```
-- MAGIC
-- MAGIC That literal is **not** something you can reuse: your `companies` table was
-- MAGIC created moments ago, when you ran the previous notebook - not in January 2025.
-- MAGIC Because that timestamp almost certainly predates the table's own `CREATE TABLE`
-- MAGIC commit, running it as-is will fail with an error to the effect of *"the provided
-- MAGIC timestamp is before the earliest version available"* - Delta has no version of
-- MAGIC the table to reconstruct before it existed. Below are two ways to build a
-- MAGIC timestamp that is actually valid for **your** run.

-- COMMAND ----------

-- Illustrative only - do not uncomment and run against your own table; the literal
-- timestamp almost certainly predates when your table was created.
-- SELECT * FROM demo.delta_lake.companies
-- TIMESTAMP AS OF '2025-01-07T11:45:12.000+00:00';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### Option A - copy a real timestamp from `DESCRIBE HISTORY`
-- MAGIC
-- MAGIC Pull the exact commit timestamp for a version you care about, then paste it into
-- MAGIC a `TIMESTAMP AS OF` clause of your own.

-- COMMAND ----------

SELECT version, operation, timestamp
FROM (DESCRIBE HISTORY demo.delta_lake.companies)
WHERE version = 0;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Copy the `timestamp` value from the row above exactly as displayed (it will look
-- MAGIC something like `2026-07-23 14:02:11.000`) and use it in place of the placeholder:
-- MAGIC
-- MAGIC ```sql
-- MAGIC SELECT * FROM demo.delta_lake.companies
-- MAGIC TIMESTAMP AS OF '<paste-your-own-version-0-timestamp-here>';
-- MAGIC ```
-- MAGIC
-- MAGIC #### Option B - fetch it programmatically
-- MAGIC
-- MAGIC The cell below does the same thing without manual copy-pasting, so it actually
-- MAGIC runs correctly no matter when you execute this notebook - handy in a job or
-- MAGIC script where no one is around to read an output and paste a value:

-- COMMAND ----------

-- MAGIC %python
-- MAGIC version_0_ts = spark.sql(
-- MAGIC     "SELECT timestamp FROM (DESCRIBE HISTORY demo.delta_lake.companies) WHERE version = 0"
-- MAGIC ).collect()[0]["timestamp"]
-- MAGIC print(f"Version 0 was committed at: {version_0_ts}")
-- MAGIC
-- MAGIC display(
-- MAGIC     spark.sql(f"SELECT * FROM demo.delta_lake.companies TIMESTAMP AS OF '{version_0_ts}'")
-- MAGIC )

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Time travel by timestamp is especially useful for data-quality investigations -
-- MAGIC for example, if an upstream supplier tells you the data was last known-good at a
-- MAGIC specific time, you can query (or restore to) exactly that point without needing
-- MAGIC to know its version number.
-- MAGIC
-- MAGIC !!! Time travel has a retention window
-- MAGIC
-- MAGIC Time travel isn't retained forever. Two table properties control it:
-- MAGIC
-- MAGIC - `delta.logRetentionDuration` (default **30 days**) - how long old JSON commits
-- MAGIC   and checkpoints are kept before Delta's own log cleanup can remove them.
-- MAGIC - `delta.deletedFileRetentionDuration` (default **7 days**) - how long Parquet
-- MAGIC   files that are no longer referenced by the latest version (e.g. superseded by
-- MAGIC   an `UPDATE`, `DELETE`, or `RESTORE`) are kept on disk before `VACUUM` is
-- MAGIC   allowed to physically delete them.
-- MAGIC
-- MAGIC Running `VACUUM` deletes any data file older than its retention threshold that
-- MAGIC the current log no longer references - including files a still-valid older
-- MAGIC version needs to reconstruct its state. Once those files are physically gone,
-- MAGIC time travel (and `RESTORE`) to a version that depended on them fails, even though
-- MAGIC `DESCRIBE HISTORY` may still list that version's metadata. In production, treat
-- MAGIC `VACUUM` scheduling and retention settings as a deliberate trade-off between
-- MAGIC storage cost and how far back you can reliably time travel or roll back.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Restore the table to a previous version
-- MAGIC
-- MAGIC `RESTORE TABLE` goes further than a read-only time travel query: it actually
-- MAGIC changes what the table's **latest** version points to. Importantly, it does this
-- MAGIC by writing a **new** commit that reinstates the old version's file list - it does
-- MAGIC **not** delete or rewrite the intervening versions. History only ever grows
-- MAGIC forward, which is also why a table that has been restored can itself still be
-- MAGIC restored to a version that came *after* the restore.
-- MAGIC
-- MAGIC Since restore normally just points the log back at Parquet files that already
-- MAGIC exist, it is typically fast - a metadata operation, not a data rewrite. The
-- MAGIC exception is exactly the retention caveat above: if `VACUUM` has already deleted
-- MAGIC the files the target version needs, `RESTORE` cannot succeed, because the data
-- MAGIC itself is gone, not just unreferenced.

-- COMMAND ----------

RESTORE TABLE demo.delta_lake.companies VERSION AS OF 1;

-- COMMAND ----------

-- Back to a single row (Apple only), matching version 1.
SELECT * FROM demo.delta_lake.companies;

-- COMMAND ----------

DESCRIBE HISTORY demo.delta_lake.companies;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC Notice version `3`, operation `RESTORE` - a brand-new commit was appended.
-- MAGIC Versions `0`-`2` are still listed exactly as before: nothing was erased. If you
-- MAGIC needed the four-row state back, `RESTORE TABLE ... VERSION AS OF 2` (or
-- MAGIC `SELECT * ... VERSION AS OF 2`) would still work right now.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Why this matters in production
-- MAGIC
-- MAGIC This is what makes Delta tables safe to operate on: a bad load can be rolled
-- MAGIC back with `RESTORE TABLE` in seconds instead of a slow reload from a backup;
-- MAGIC every change is already an auditable row in `DESCRIBE HISTORY` with no extra
-- MAGIC logging to build; and a `VERSION AS OF`/`TIMESTAMP AS OF` snapshot gives you a
-- MAGIC reproducible input for things like ML model training or a regulator asking "what
-- MAGIC did this data look like on a specific date" - as long as it's still inside the
-- MAGIC retention window above.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary
-- MAGIC
-- MAGIC - `DESCRIBE HISTORY` surfaces the `_delta_log` commit metadata: version, user,
-- MAGIC   timestamp, and operation for every change.
-- MAGIC - `VERSION AS OF` / `TIMESTAMP AS OF` reconstruct a past state by replaying the
-- MAGIC   log up to that point - no data copying involved.
-- MAGIC - A hardcoded timestamp literal from a tutorial will not match your own run;
-- MAGIC   pull a real one from your table's own `DESCRIBE HISTORY` instead.
-- MAGIC - Time travel has a retention window (`delta.logRetentionDuration`,
-- MAGIC   `delta.deletedFileRetentionDuration`), and `VACUUM` can permanently end it
-- MAGIC   early by deleting files an older version still needs.
-- MAGIC - `RESTORE TABLE` rolls back by adding a new commit, not by deleting history -
-- MAGIC   the table's full version history keeps growing forward.
