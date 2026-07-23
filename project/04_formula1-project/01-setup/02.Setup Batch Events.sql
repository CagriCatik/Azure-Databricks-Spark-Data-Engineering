-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Setup Batch Events
-- MAGIC 1. Create control schema
-- MAGIC 1. Create batch_events table
-- MAGIC 1. Insert an event record
-- MAGIC
-- MAGIC > **Not part of this project's pipeline.** This `04_formula1-project`
-- MAGIC > implementation is a **full-refresh** pipeline: every bronze notebook in
-- MAGIC > `02-bronze` loads its entire source file with `.mode('overwrite')` on
-- MAGIC > every run, and neither `00-common/01.environment-config` nor
-- MAGIC > `00-common/02.bronze-helpers` reference a `batch_id`, a `control` schema,
-- MAGIC > or this table anywhere. Creating this schema/table is **safe** (nothing
-- MAGIC > else in this project reads or writes `formula1.control.batch_events`),
-- MAGIC > but it is also **inert** here - it demonstrates, in isolation, the shape
-- MAGIC > of the batch-tracking control table used for real incremental
-- MAGIC > orchestration in the companion project,
-- MAGIC > `project/05_formula1-project-incremental-load`, which drives its Delta
-- MAGIC > `MERGE` loads off a genuine control schema. Treat this notebook as a
-- MAGIC > standalone concept demo, not a step you need to run for `04_formula1-project`
-- MAGIC > to work end to end.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 1. Create control schema
-- MAGIC
-- MAGIC Its own schema (and managed location) for the same reason `bronze`,
-- MAGIC `silver`, and `gold` each get one in
-- MAGIC `01-setup/01.Setup Project Environment.sql`: control/orchestration
-- MAGIC metadata is a distinct concern from the medallion data layers and should
-- MAGIC be stored, secured, and reasoned about separately.

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS formula1.control
COMMENT 'Control and orchestration metadata for the Formula 1 project';

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 2. Create batch_events table
-- MAGIC
-- MAGIC Minimal event log: one row per batch, recording when that batch was
-- MAGIC processed. A real control-table design (see project 05) typically also
-- MAGIC tracks per-table watermarks (e.g. last successfully loaded timestamp or
-- MAGIC key) so an incremental load knows exactly which rows to pick up next;
-- MAGIC this table only demonstrates the event-log half of that pattern.

-- COMMAND ----------



-- Create the managed Delta table.
CREATE TABLE IF NOT EXISTS formula1.control.batch_events
(
    batch_id        INT,
    event_timestamp TIMESTAMP
)
USING DELTA
COMMENT 'Records Formula 1 batch-processing events';

-- 3. Verify the objects.
SHOW SCHEMAS IN formula1;

DESCRIBE TABLE EXTENDED formula1.control.batch_events;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### 3. Insert an event record
-- MAGIC
-- MAGIC Two sample rows just to demonstrate the insert pattern - `batch_id` is a
-- MAGIC plain literal here, not generated from any sequence or upstream job
-- MAGIC parameter, since no orchestrator in this project actually assigns one.

-- COMMAND ----------

INSERT INTO formula1.control.batch_events
VALUES (1, current_timestamp());

-- COMMAND ----------

INSERT INTO formula1.control.batch_events
VALUES (2, current_timestamp());

-- COMMAND ----------

SELECT * FROM formula1.control.batch_events;
