# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Merge Helper
# MAGIC
# MAGIC Shared helper used by every notebook in `04-gold` to upsert a
# MAGIC dimension/fact batch into its gold Delta table. Import with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/04.gold-helpers
# MAGIC ```
# MAGIC
# MAGIC Structurally almost identical to `write_to_silver` in
# MAGIC `03.silver-helpers` - same create-or-merge shape, same
# MAGIC `created_timestamp`/`updated_timestamp` handling. The one deliberate
# MAGIC difference is documented in the function docstring below: gold's
# MAGIC `whenMatchedUpdate` has no batch-recency guard, and that is currently a
# MAGIC real limitation rather than a design choice.

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from delta.tables import DeltaTable


def write_to_gold(
    input_df: DataFrame,
    target_table: str,
    merge_condition: str,
    columns_to_update: list
) -> None:
    """Create-or-merge a transformed batch into a gold Delta table.

    Same create-or-merge shape as `write_to_silver`: writes the table
    directly via `saveAsTable` on first run, and performs a Delta `MERGE`
    (`whenNotMatchedInsertAll` / `whenMatchedUpdate`) on every run after
    that. `created_timestamp` is stamped once and excluded from
    `columns_to_update` so it survives re-merges untouched; `updated_timestamp`
    is recomputed and applied on every merge. See `write_to_silver` in
    `00-common/03.silver-helpers` for the full rationale behind both columns.

    KNOWN GAP - no batch-recency guard on the merge:

    `write_to_silver`'s `whenMatchedUpdate` is guarded with
    `condition="s.batch_id >= t.batch_id"`, so an out-of-order rerun of an
    older batch can never overwrite a row a newer batch already updated.
    This function's `whenMatchedUpdate` below has **no such condition** - it
    updates matched rows unconditionally, regardless of which batch they
    came from.

    This is a documented limitation, not an oversight to silently patch
    here: `batch_id` is not carried through to the gold layer at all. The
    caller in this project (`04-gold/04.Build Results Fact.py`) explicitly
    drops `batch_id` from its DataFrame before calling `write_to_gold`,
    because the gold fact table's own schema does not include that column.
    Adding the same `s.batch_id >= t.batch_id` guard here today would
    reference a column that does not exist on either side of the merge and
    would fail at runtime - so it is intentionally left out rather than
    added incorrectly.

    If protecting gold against an out-of-order batch rerun is ever needed,
    the fix is to thread `batch_id` through silver into every gold source
    DataFrame (a schema change to the relevant silver/gold tables) and only
    then add the equivalent guard to this function's `whenMatchedUpdate`.
    Until that happens, gold merges implicitly trust that batches are
    always replayed in non-decreasing `batch_id` order.

    Args:
        input_df: Transformed batch DataFrame for the gold table. Must not
            rely on a `batch_id` column being present - see the gap above.
        target_table: Fully qualified target table name
            (`catalog.schema.table`).
        merge_condition: SQL boolean expression used as the Delta `MERGE ON`
            clause (aliases `s` = source/incoming, `t` = target/existing).
        columns_to_update: Column names to overwrite unconditionally on a
            matched row. `updated_timestamp` is added automatically and
            should not be included in this list.
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
                set=update_map
            )
            .whenNotMatchedInsertAll()
            .execute()
        )
