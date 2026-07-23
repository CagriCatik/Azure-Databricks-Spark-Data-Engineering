# Databricks notebook source
# MAGIC %md
# MAGIC # Create New Batch
# MAGIC
# MAGIC Registers `p_batch_id` as `in_progress` in `batch_control`. In the job
# MAGIC graph this runs right after `01.Identify Next Batch` determines there is a
# MAGIC new batch to process (typically parameterized from that task's
# MAGIC `p_batch_id` task value, wired up in the Jobs UI), and before any
# MAGIC bronze/silver/gold notebook processes that batch's data.
# MAGIC
# MAGIC This is a plain `append`, not a merge — by the time this notebook runs,
# MAGIC `01.Identify Next Batch` has already confirmed `p_batch_id` is not yet
# MAGIC tracked in `batch_control`, so there is no existing row to reconcile
# MAGIC against. That also means this notebook is **not** safe to rerun for the
# MAGIC same `batch_id`: appending again would insert a second `in_progress` row
# MAGIC for it. The job graph should invoke this exactly once per batch;
# MAGIC rerun-safety for the rest of the state machine instead comes from the
# MAGIC guarded `MERGE` in `03.Complete Batch`.

# COMMAND ----------

# MAGIC %md
# MAGIC ![Incremental Data Processing](../../z-course-images/formula1-incremental-data-processing.png "Incremental Data Processing")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

control_table = f"{catalog_name}.{control_schema}.batch_control"

# COMMAND ----------

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

from pyspark.sql import Row
from pyspark.sql import functions as F

# Plain append: batch_id is expected to be new/untracked at this point (see
# 01.Identify Next Batch), so there is no existing row to merge against. This
# intentionally doesn't use write_to_gold/write_to_silver — those helpers are
# for dimensional/fact merges keyed by business columns, whereas this is
# simple control-table bookkeeping (one insert per batch).
if v_batch_id:
    in_progress_df = (
        spark.createDataFrame(
            [Row(batch_id=v_batch_id, status="in_progress")]
        )
        .withColumn("created_timestamp", F.current_timestamp())
        .withColumn("updated_timestamp", F.current_timestamp())
    )

    (
        in_progress_df.write
            .format("delta")
            .mode("append")
            .saveAsTable(control_table)
    )

    print(f"Marked batch {v_batch_id} as in_progress")
else:
    raise Exception("batch_id is missing")  