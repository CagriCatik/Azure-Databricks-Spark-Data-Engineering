# Databricks notebook source
# MAGIC %md
# MAGIC # Create Control Tables
# MAGIC
# MAGIC Creates the `control` schema and the `batch_control` table that drives
# MAGIC batch orchestration for the rest of `06-orchestration`:
# MAGIC `formula1_incr.control.batch_control (batch_id STRING, status STRING,
# MAGIC created_timestamp TIMESTAMP, updated_timestamp TIMESTAMP)`. Every
# MAGIC downstream orchestration notebook (`01.Identify Next Batch`,
# MAGIC `02.Create New Batch`, `03.Complete Batch`) reads or writes this exact
# MAGIC table.
# MAGIC
# MAGIC > **Not to be confused with `batch_events`.** `01-setup/02.Setup Batch Events`
# MAGIC > creates a separate, unrelated table —
# MAGIC > `control.batch_events (batch_id INT, event_timestamp TIMESTAMP)` — as a
# MAGIC > standalone demo of writing into a control schema. It is never read or
# MAGIC > written by any notebook in `06-orchestration` and plays no part in how
# MAGIC > batches are actually tracked. `batch_control` (created here) is the real
# MAGIC > state store behind the batch state machine (`in_progress` ->
# MAGIC > `completed`); `batch_events` is not.
# MAGIC
# MAGIC Both the `CREATE SCHEMA IF NOT EXISTS` and `CREATE TABLE IF NOT EXISTS`
# MAGIC statements below are idempotent — rerunning this notebook against an
# MAGIC environment that's already set up is always safe and never touches
# MAGIC existing rows in `batch_control`.

# COMMAND ----------

# MAGIC %md
# MAGIC ![Incremental Data Processing](../../z-course-images/formula1-incremental-data-processing.png "Incremental Data Processing")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{control_schema}")

# COMMAND ----------

spark.sql(f"""
          CREATE TABLE IF NOT EXISTS {catalog_name}.{control_schema}.batch_control
            (
                batch_id STRING,
                status STRING,
                created_timestamp TIMESTAMP,
                updated_timestamp TIMESTAMP
            )
          """)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Ad hoc testing cells (not part of setup)
# MAGIC The two cells below are **not** required steps of the control-table setup
# MAGIC — they are interactive helpers for inspecting or resetting state while
# MAGIC developing/testing the pipeline. Run the `SELECT` freely to inspect the
# MAGIC current batch state. Only run the `DELETE` if you deliberately want to
# MAGIC wipe `batch_control` and restart batch processing from scratch (e.g. while
# MAGIC testing) — in a real environment this would erase the record of every
# MAGIC batch already processed, and every landing batch would look "new" again
# MAGIC to `01.Identify Next Batch`.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM formula1_incr.control.batch_control;

# COMMAND ----------

# MAGIC %sql
# MAGIC DELETE FROM formula1_incr.control.batch_control;