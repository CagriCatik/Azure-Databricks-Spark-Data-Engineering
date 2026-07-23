# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Ingestion Helpers
# MAGIC
# MAGIC Shared helpers used by every notebook in `02-bronze`. Import with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/02.bronze-helpers
# MAGIC ```
# MAGIC
# MAGIC Two responsibilities live here:
# MAGIC
# MAGIC - `add_ingestion_metadata` - stamp every row with lineage metadata
# MAGIC   (`ingestion_timestamp`, `source_file`). Identical to the full-refresh
# MAGIC   project's helper of the same name.
# MAGIC - `write_to_bronze` - the incremental-specific write path. It writes
# MAGIC   only the Delta partition belonging to the current `batch_id`, leaving
# MAGIC   every other batch's data in the table untouched, which is what makes
# MAGIC   a bronze notebook safe to rerun for a single batch.

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_ingestion_metadata(df: DataFrame) -> DataFrame:
    """Stamp a raw source DataFrame with bronze-layer lineage metadata.

    Adds two columns that make the bronze layer auditable - for any row you
    can always answer "which file did this come from, and when did we load
    it?" without re-reading the source system:

    - ``ingestion_timestamp``: wall-clock time this DataFrame was processed,
      via ``current_timestamp()``.
    - ``source_file``: the exact file each row was read from, taken from
      Spark's built-in ``_metadata.file_path`` column (populated
      automatically for file-based sources - no manual bookkeeping needed).

    Args:
        df: Source DataFrame read directly from a file-based format
            (CSV/JSON/...), before any bronze table write.

    Returns:
        The same DataFrame with ``ingestion_timestamp`` and ``source_file``
        columns appended. Existing columns and row values are untouched.
    """
    return (
        df.withColumn('ingestion_timestamp', F.current_timestamp())
          .withColumn('source_file', F.col('_metadata.file_path'))
    )

# COMMAND ----------

def write_to_bronze(
    input_df: DataFrame,
    target_table: str,
    batch_id: str
) -> None:
    """Write one batch's rows into a bronze Delta table, touching only that
    batch's own partition.

    Tags every row with a literal ``batch_id`` column, then writes with:

    - ``.partitionBy('batch_id')`` - the table is physically partitioned by
      batch, so each batch's rows live in their own partition directory.
    - ``.mode('overwrite')`` together with
      ``.option('replaceWhere', "batch_id = '<id>'")`` - a *partition-scoped*
      overwrite. Delta only deletes and replaces the partition matching this
      exact ``batch_id``; every other partition (i.e. every other batch
      already loaded into this table) is left completely untouched.

    Together, this combination is what makes bronze ingestion
    idempotent-and-safe to rerun for a single batch: re-running this
    notebook for ``batch_id='3'`` only ever rewrites the ``batch_id=3``
    partition, so it can never corrupt or lose data from batches 1, 2, 4, ...
    already sitting in the table. Without ``replaceWhere``, a plain
    ``.mode('overwrite')`` would truncate the *entire* table on every run -
    exactly what the full-refresh project's bronze layer does on purpose,
    and exactly what this project must avoid.

    Args:
        input_df: DataFrame for a single batch, already carrying the
            lineage columns added by `add_ingestion_metadata`.
        target_table: Fully qualified target table name
            (`catalog.schema.table`). Created automatically on first write.
        batch_id: The batch identifier for this run (typically the
            `p_batch_id` widget value). Stamped onto every row and used as
            the partition predicate for the scoped overwrite.
    """
    final_df = input_df.withColumn("batch_id", F.lit(batch_id))
    (
        final_df
            .write
            .format('delta')
            .mode('overwrite')
            .partitionBy('batch_id')
            .option('replaceWhere', f"batch_id = '{batch_id}'")
            .saveAsTable(target_table)
    )
