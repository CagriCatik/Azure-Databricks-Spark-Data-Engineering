# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest circuits.csv file
# MAGIC 1. Read the file using spark dataframe reader API
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This is a **bronze** notebook: its only job is to land `circuits.csv` into
# MAGIC Delta with full fidelity and minimal transformation - no filtering,
# MAGIC deduplication, joins, or type coercion beyond parsing the declared schema.
# MAGIC Circuits is reference/lookup data (one row per circuit, rarely changes), so
# MAGIC a full overwrite on every run is cheap and simple; the more interesting
# MAGIC data-quality reasoning here is the strict, explicit schema in Step 1.
# MAGIC
# MAGIC This project (`04_formula1-project`) is a **full-refresh** pipeline: this
# MAGIC notebook always replaces the entire bronze table (`.mode('overwrite')`),
# MAGIC with no batch tracking or incremental merge. See
# MAGIC `project/05_formula1-project-incremental-load` for the same pipeline
# MAGIC re-architected around Delta `MERGE` and a control-table watermark.

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/02.bronze-helpers

# COMMAND ----------

source_file = f"{landing_folder_path}/circuits.csv"
table_name = f"{catalog_name}.{bronze_schema}.circuits"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the CSV file using the dataframe reader API
# MAGIC
# MAGIC `circuits.csv` columns: `circuitId`, `url`, `circuitName`, `lat`, `long`,
# MAGIC `locality`, `country`.
# MAGIC
# MAGIC The schema is declared explicitly and `inferSchema` is deliberately left
# MAGIC off (see the commented-out option below). `inferSchema` forces Spark to
# MAGIC read the file twice - once to sample and guess types, once to actually
# MAGIC load it - and its guess can silently change between runs if the data
# MAGIC shifts (e.g. a normally-numeric `circuitId` column that gets one
# MAGIC alphanumeric value would flip the inferred type of the whole column).
# MAGIC An explicit `StructType` makes the contract for this bronze table
# MAGIC stable and reviewable in code, instead of implicit and file-dependent.
# MAGIC
# MAGIC `mode('FAILFAST')` complements this: if any row does not conform to the
# MAGIC declared schema, the read raises immediately instead of silently writing
# MAGIC `NULL`s (the default `PERMISSIVE` mode) or dropping the offending rows
# MAGIC (`DROPMALFORMED`). For a bronze layer that downstream silver/gold
# MAGIC notebooks trust as the raw source of truth, a loud failure here is far
# MAGIC preferable to quietly corrupting or truncating the data.

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DoubleType

circuits_schema = StructType([
    StructField('circuitId',   StringType()),
    StructField("url",         StringType()),
    StructField("circuitName", StringType()),
    StructField("lat",         DoubleType()),
    StructField("long",        DoubleType()),
    StructField("locality",    StringType()),
    StructField("country",     StringType())
])

# COMMAND ----------

circuits_df = (
    spark.read
         .format('csv')
         .option('header', 'true')
#         .option('inferSchema', 'true')
         .option('mode', 'FAILFAST')
         .schema(circuits_schema)
         .load(source_file)
)

# COMMAND ----------

display(circuits_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Add Metadata Columns
# MAGIC - Source File
# MAGIC - Ingestion Timestamp
# MAGIC
# MAGIC `add_ingestion_metadata` (from `00-common/02.bronze-helpers`) appends
# MAGIC `source_file` (from Spark's built-in `_metadata.file_path`) and
# MAGIC `ingestion_timestamp` (`current_timestamp()`). These two columns are what
# MAGIC make this bronze table auditable: given any row, you can trace it back to
# MAGIC the exact file it came from and know precisely when it was loaded.

# COMMAND ----------

circuits_final_df = add_ingestion_metadata(circuits_df)

# COMMAND ----------

display(circuits_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.circuits` table
# MAGIC on every run - consistent with this project's full-refresh design. This
# MAGIC is a reasonable trade-off for small, slowly-changing reference data like
# MAGIC circuits, where re-reading and rewriting the whole file every run costs
# MAGIC little.

# COMMAND ----------

(
    circuits_final_df
        .write
        .format('delta')
        .mode('overwrite')
        .saveAsTable(table_name)
)

# COMMAND ----------

display(spark.table(table_name))

# COMMAND ----------

# MAGIC %md
# MAGIC #### Sanity check - row counts should match
# MAGIC
# MAGIC A full-refresh `overwrite` should preserve row count exactly: every row
# MAGIC read from `circuits.csv` should land in the bronze table. `FAILFAST`
# MAGIC already guarantees the source read itself is either complete or raises,
# MAGIC so a mismatch here would point to a bug in the write path rather than in
# MAGIC the source file.

# COMMAND ----------

source_row_count = circuits_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
