# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Merge Helper
# MAGIC
# MAGIC Shared helper used by every notebook in `03-silver` to upsert a
# MAGIC transformed batch into its silver Delta table. Import with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/03.silver-helpers
# MAGIC ```
# MAGIC
# MAGIC Unlike bronze (a partition-scoped overwrite per batch), silver upserts
# MAGIC row by row with a Delta `MERGE`, keyed on a caller-supplied
# MAGIC `merge_condition` (typically the natural/business key). That is what
# MAGIC lets a batch containing only a handful of changed or new rows update
# MAGIC just those rows in an already-large silver table, instead of
# MAGIC rewriting an entire partition.

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from delta.tables import DeltaTable


def write_to_silver(
    input_df: DataFrame,
    target_table: str,
    merge_condition: str,
    columns_to_update: list
) -> None:
    """Create-or-merge a transformed batch into a silver Delta table.

    First run (table does not exist yet): the DataFrame is written as-is via
    `saveAsTable` - there is nothing to merge against yet.

    Every run after that: performs a Delta `MERGE` -
    `whenNotMatchedInsertAll()` for genuinely new keys, and
    `whenMatchedUpdate` for keys that already exist, guarded by
    `condition="s.batch_id >= t.batch_id"`.

    That guard is the important part. It only lets an incoming row overwrite
    an existing row when the incoming batch is the same as, or newer than,
    the batch that last wrote that row (`s` = source/incoming batch, `t` =
    target/existing row already in the table). Without it, re-running or
    backfilling an *older* batch out of order - after a newer batch has
    already updated the same key - would silently clobber the newer values
    with stale ones. With the guard in place, an out-of-order rerun of an
    older batch simply loses the update race on any row a newer batch
    already touched, which is the correct, safe outcome. This relies on
    `batch_id` already being a column on both sides of the merge, i.e. every
    silver source DataFrame must ultimately derive from a bronze table
    written by `write_to_bronze`.

    `created_timestamp` / `updated_timestamp` semantics:

    - `created_timestamp` is stamped once, from `current_timestamp()` at
      write time, and is deliberately **not** included in
      `columns_to_update` - so it is only ever set by
      `whenNotMatchedInsertAll()` the first time a key is seen, and is never
      touched again on later merges. Re-merging the same key on a
      subsequent batch never overwrites its original creation time.
    - `updated_timestamp` is recomputed on every call and is added to
      `update_map` explicitly, so it always reflects the last time this key
      was merged, whether that merge was an insert or an update.

    Args:
        input_df: Transformed batch DataFrame, expected to carry a
            `batch_id` column sourced from bronze.
        target_table: Fully qualified target table name
            (`catalog.schema.table`).
        merge_condition: SQL boolean expression used as the Delta `MERGE ON`
            clause (aliases `s` = source/incoming, `t` = target/existing),
            e.g. `"s.circuit_id = t.circuit_id"`.
        columns_to_update: Column names to overwrite on a matched row once
            the batch-recency guard passes. `updated_timestamp` is added
            automatically and should not be included in this list.
    """

    final_df = (
        input_df
        .withColumn("created_timestamp", F.current_timestamp())
        .withColumn("updated_timestamp", F.current_timestamp())
    )

    if not spark.catalog.tableExists(target_table):
        (
            final_df.write
                .format("delta")
                .mode("overwrite")
                .saveAsTable(target_table)
        )
    else:
        delta_table = DeltaTable.forName(spark, target_table)
        update_map = {column: f"s.{column}" for column in columns_to_update}
        update_map["updated_timestamp"] = "s.updated_timestamp"

        (
            delta_table.alias("t")
            .merge(
                final_df.alias("s"),
                merge_condition
            )
            .whenMatchedUpdate(
                condition="s.batch_id >= t.batch_id",
                set=update_map
            )
            .whenNotMatchedInsertAll()
            .execute()
        )
