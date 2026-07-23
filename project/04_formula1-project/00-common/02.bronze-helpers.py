# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Ingestion Helpers
# MAGIC
# MAGIC Shared helper used by every notebook in `02-bronze` to stamp incoming data
# MAGIC with lineage metadata before it is written down as a bronze Delta table.
# MAGIC Import it with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/02.bronze-helpers
# MAGIC ```
# MAGIC
# MAGIC Keeping this in one place means every bronze table gets the exact same two
# MAGIC columns, named the same way, computed the same way - so silver notebooks
# MAGIC downstream can always rely on `ingestion_timestamp` and `source_file` being
# MAGIC present, regardless of which bronze notebook produced the table.

# COMMAND ----------

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_ingestion_metadata(df: DataFrame) -> DataFrame:
    """Stamp a raw source DataFrame with bronze-layer lineage metadata.

    Adds two columns that make the bronze layer auditable - i.e. for any row,
    you can always answer "which file did this come from, and when did we load
    it?" without re-reading the source system:

    - ``ingestion_timestamp``: wall-clock time this DataFrame was processed,
      via ``current_timestamp()``. Lets you tell how fresh (or stale) a bronze
      table is, and lets multiple runs of the same full-refresh load be told
      apart even though the row values themselves may be identical.
    - ``source_file``: the exact file each row was read from, taken from
      Spark's built-in ``_metadata.file_path`` column (populated automatically
      for file-based sources such as CSV/JSON - no manual bookkeeping needed).
      Essential for tracing a bad or unexpected row back to the physical file
      it came from, especially once a landing folder holds many files (e.g.
      the multi-file `results`/`sprints` sources ingested elsewhere in this
      project).

    Args:
        df: Source DataFrame read directly from a file-based format
            (CSV/JSON/Parquet/...), before any bronze table write.

    Returns:
        The same DataFrame with ``ingestion_timestamp`` and ``source_file``
        columns appended. Existing columns and row values are untouched.
    """
    return (
        df.withColumn('ingestion_timestamp', F.current_timestamp())
          .withColumn('source_file', F.col('_metadata.file_path'))
    )
