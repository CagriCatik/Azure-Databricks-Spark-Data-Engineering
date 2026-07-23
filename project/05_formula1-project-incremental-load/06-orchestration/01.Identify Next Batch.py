# Databricks notebook source
# MAGIC %md
# MAGIC # Identify Next Batch
# MAGIC
# MAGIC Scans the landing volume for batch folders that are not yet tracked in
# MAGIC `batch_control`, and publishes the earliest untracked `batch_id` as
# MAGIC Databricks Job task values for the next task in the workflow to consume.
# MAGIC
# MAGIC > **`dbutils.jobs.taskValues` only works inside a Databricks Job.** Calling
# MAGIC > `taskValues.set(...)` during an ad hoc/interactive run of this notebook
# MAGIC > (e.g. "Run all" in the notebook editor) executes without error but has no
# MAGIC > effect — there is no downstream job task to receive the value, and
# MAGIC > nothing else in this notebook reads it back. The mechanism only does
# MAGIC > something when this notebook runs as a **task** inside a Databricks
# MAGIC > Workflow/Job.
# MAGIC >
# MAGIC > When it *is* run as a job task, the values set here (keyed `p_batch_id`
# MAGIC > and `has_batch`) become readable by any task configured to run **after**
# MAGIC > this one in the same job run, via a task-value reference such as
# MAGIC > `{{tasks.<this_task_name>.values.p_batch_id}}`. That reference has to be
# MAGIC > entered as the downstream task's `p_batch_id` parameter value (which then
# MAGIC > lands in its `p_batch_id` widget) when configuring the task in the
# MAGIC > **Databricks Jobs UI** — none of that task-graph wiring exists in, or can
# MAGIC > be inferred from, this notebook's code. A learner reading only this file
# MAGIC > should understand that the actual dependency graph — which tasks run
# MAGIC > after this one, what conditions gate them, and which task-value keys feed
# MAGIC > which downstream parameters — is configured separately in the Jobs UI,
# MAGIC > not here.
# MAGIC >
# MAGIC > `has_batch` is intended to drive a downstream **condition / "Run if"**
# MAGIC > check in the job graph, so the batch-processing tasks (bronze, silver,
# MAGIC > gold, then `02.Create New Batch`) can be skipped entirely on a run where
# MAGIC > there's nothing new to process — again, that condition task/setting lives
# MAGIC > in the Jobs UI, not in this code.

# COMMAND ----------

# MAGIC %md
# MAGIC ![Incremental Data Processing](../../z-course-images/formula1-incremental-data-processing.png "Incremental Data Processing")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

control_table = f"{catalog_name}.{control_schema}.batch_control"

# COMMAND ----------

from pyspark.sql import functions as F

# Get batch folders from landing. Sorting assumes the batch-folder naming
# convention (e.g. batch_001, batch_002, ... or a date-based name) sorts
# lexicographically in the same order batches should be processed — a plain
# string sort is only correct because of that naming convention.
landing_batches = sorted([
    file.name.rstrip("/")
    for file in dbutils.fs.ls(landing_folder_path)
    if file.isDir()
])

# Read tracked batches. Both "in_progress" and "completed" count as tracked,
# not just "completed" — this stops a batch from being picked up a second
# time while it is still being processed. The trade-off: if a batch is ever
# left stuck "in_progress" (e.g. a failed job run that never reached
# 03.Complete Batch), it will never be retried automatically by this logic;
# someone has to intervene (e.g. fix/reset its batch_control row) before it
# can be reprocessed.
if spark.catalog.tableExists(control_table):
    tracked_batches = [
        row.batch_id
        for row in (
            spark.table(control_table)
                 .filter(F.col("status").isin("in_progress", "completed"))
                 .select("batch_id")
                 .distinct()
                 .collect()
        )
    ]
else:
    tracked_batches = []

# Identify earliest unprocessed batch. Only one batch is surfaced per job
# run, keeping each pipeline run's blast radius to exactly one batch.
new_batches = sorted(list(set(landing_batches) - set(tracked_batches)))
next_batch = new_batches[0] if new_batches else None

print(f"Landing batches     : {landing_batches}")
print(f"Tracked batches     : {tracked_batches}")
print(f"Next batch to process: {next_batch}")

# Publish the result as job task values. As noted above, this only has an
# effect when this notebook executes as a task inside a Databricks Job — the
# downstream task graph that consumes p_batch_id / has_batch is configured
# in the Databricks Jobs UI, not in this notebook.
if next_batch is None:
    dbutils.jobs.taskValues.set(key="p_batch_id", value="")
    dbutils.jobs.taskValues.set(key="has_batch", value="false")
else:
    dbutils.jobs.taskValues.set(key="p_batch_id", value=next_batch)
    dbutils.jobs.taskValues.set(key="has_batch", value="true")