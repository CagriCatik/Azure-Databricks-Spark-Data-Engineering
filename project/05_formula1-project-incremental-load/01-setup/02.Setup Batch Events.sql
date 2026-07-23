-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Setup Batch Events
-- MAGIC 1. Create control schema
-- MAGIC 1. Create batch_events table
-- MAGIC 1. Insert an event record
-- MAGIC
-- MAGIC > **Not the pipeline's real control table.** `batch_events` here is a
-- MAGIC > small, standalone illustration of the idea of a batch/event log -
-- MAGIC > one row per batch, with a timestamp. It is a **different table**
-- MAGIC > from `formula1_incr.control.batch_control`
-- MAGIC > (`batch_id STRING, status STRING, created_timestamp, updated_timestamp`),
-- MAGIC > which is the table `06-orchestration` actually creates and reads
-- MAGIC > from/writes to in order to drive the real pipeline:
-- MAGIC > `01.Identify Next Batch.py` queries it to decide which batch to run
-- MAGIC > next, `02.Create New Batch.py` inserts a new in-flight row, and
-- MAGIC > `03.Complete Batch.py` marks it done. Nothing in `02-bronze`,
-- MAGIC > `03-silver`, or `04-gold` reads or writes `batch_events` - do not
-- MAGIC > confuse the two tables, and do not expect running this notebook to
-- MAGIC > have any effect on the real orchestration flow.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 1. Create control schema
-- MAGIC
-- MAGIC The same `control` schema referenced by `control_schema` in
-- MAGIC `00-common/01.environment-config` and created (if not already
-- MAGIC present) by `06-orchestration/00.Create Control Tables.py`.
-- MAGIC `IF NOT EXISTS` makes this notebook safe to run in either order
-- MAGIC relative to that one.

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS formula1_incr.control
    MANAGED LOCATION 'abfss://formula1-incr@databrickscourseextdl1.dfs.core.windows.net/control';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 2. Create batch_events table
-- MAGIC
-- MAGIC Minimal event log: one row per batch, recording when that batch was
-- MAGIC processed. Compare this to the real `batch_control` table described
-- MAGIC above, which additionally tracks a `status` per batch so an
-- MAGIC orchestrator can tell which batch is in flight versus completed -
-- MAGIC this table only demonstrates the append-only event-log half of that
-- MAGIC idea.

-- COMMAND ----------

CREATE TABLE IF NOT EXISTS formula1_incr.control.batch_events
(
    batch_id INT,
    event_timestamp TIMESTAMP
)

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 3. Insert an event record

-- COMMAND ----------

INSERT INTO formula1_incr.control.batch_events
VALUES (1, current_timestamp());

-- COMMAND ----------

INSERT INTO formula1_incr.control.batch_events
VALUES (2, current_timestamp());

-- COMMAND ----------

SELECT * FROM formula1_incr.control.batch_events;
