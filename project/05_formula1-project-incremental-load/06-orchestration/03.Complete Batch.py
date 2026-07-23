# Databricks notebook source
# MAGIC %md
# MAGIC # Complete Batch
# MAGIC
# MAGIC Flips `p_batch_id`'s row in `batch_control` from `in_progress` to
# MAGIC `completed`, once every bronze/silver/gold notebook has finished
# MAGIC processing that batch. This is the last task in the per-batch job graph.
# MAGIC
# MAGIC The merge condition is `t.batch_id = s.batch_id AND t.status = 'in_progress'`
# MAGIC — that extra `t.status = 'in_progress'` guard is what makes this notebook
# MAGIC safe to rerun:
# MAGIC - If the batch is genuinely `in_progress`, the merge matches and flips it
# MAGIC   to `completed`.
# MAGIC - If it has already been marked `completed` (this task already ran once,
# MAGIC   or the job retried it), the guard no longer matches, so rerunning is a
# MAGIC   harmless no-op instead of a duplicate/confusing update.
# MAGIC - If `batch_id` was never registered as `in_progress` at all (e.g.
# MAGIC   `02.Create New Batch` never ran for it), the merge simply matches
# MAGIC   nothing. There is no `whenNotMatchedInsert` here, so this notebook can
# MAGIC   never create a `batch_control` row on its own — it only ever transitions
# MAGIC   an existing `in_progress` row to `completed`.

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

from delta.tables import DeltaTable
from pyspark.sql import functions as F

if v_batch_id:
    delta_table = DeltaTable.forName(spark, control_table)

    source_df = (
        spark.createDataFrame([(v_batch_id,)], ["batch_id"])
            .withColumn("status", F.lit("completed"))
            .withColumn("updated_timestamp", F.current_timestamp())
    )

    (
        delta_table.alias("t")
            .merge(
                source_df.alias("s"),
                "t.batch_id = s.batch_id AND t.status = 'in_progress'"
            )
            .whenMatchedUpdate(set={
                "status": "s.status",
                "updated_timestamp": "s.updated_timestamp"
            })
            .execute()
    )

    print(f"Marked batch {v_batch_id} as completed")
else:
    raise Exception("batch_id is missing")  