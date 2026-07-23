# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest races.csv file
# MAGIC 1. Read the file using spark dataframe reader API
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This is a **bronze** notebook: it lands `races.csv` into Delta with full
# MAGIC fidelity and minimal transformation - no filtering, deduplication, joins,
# MAGIC or derived columns beyond parsing the declared schema. Races is one row
# MAGIC per race (season + round), and this project (`04_formula1-project`) is a
# MAGIC **full-refresh** pipeline: this notebook always replaces the entire bronze
# MAGIC table (`.mode('overwrite')`), with no batch tracking or incremental merge.
# MAGIC See `project/05_formula1-project-incremental-load` for the same pipeline
# MAGIC re-architected around Delta `MERGE` and a control-table watermark.

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/02.bronze-helpers

# COMMAND ----------

source_file = f"{landing_folder_path}/races.csv"
table_name = f"{catalog_name}.{bronze_schema}.races"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the CSV file using the dataframe reader API
# MAGIC
# MAGIC `races.csv` columns: `season`, `round`, `url`, `raceName`, `date`,
# MAGIC `circuitId` - `circuitId` is the join key back to
# MAGIC `formula1.bronze.circuits`.
# MAGIC
# MAGIC The schema is declared explicitly, and `inferSchema` is deliberately left
# MAGIC off (see the commented-out option below) in favor of an explicit
# MAGIC `StructType` - this keeps the column types (in particular `date` as a real
# MAGIC `DateType`, not a guessed string) stable and reviewable in code rather than
# MAGIC re-inferred, and possibly different, on every run.
# MAGIC
# MAGIC `mode('FAILFAST')` complements this: any row that does not conform to the
# MAGIC declared schema raises immediately instead of silently writing `NULL`s
# MAGIC (the default `PERMISSIVE` mode) or dropping offending rows
# MAGIC (`DROPMALFORMED`) - a loud failure here is far preferable to quietly
# MAGIC corrupting the raw source of truth that silver notebooks build on.

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType

races_schema = StructType([
    StructField('season',   IntegerType()),
    StructField("round",    IntegerType()),
    StructField("url",      StringType()),
    StructField("raceName", StringType()),
    StructField("date",     DateType()),
    StructField("circuitId", StringType())
])

# COMMAND ----------

races_df = (
    spark.read
         .format('csv')
         .option('header', 'true')
#         .option('inferSchema', 'true')
         .option('mode', 'FAILFAST')
         .schema(races_schema)
         .load(source_file)
)

# COMMAND ----------

display(races_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Add Metadata Columns
# MAGIC - Source File
# MAGIC - Ingestion Timestamp
# MAGIC
# MAGIC `add_ingestion_metadata` (from `00-common/02.bronze-helpers`) appends
# MAGIC `source_file` (from Spark's built-in `_metadata.file_path`) and
# MAGIC `ingestion_timestamp` (`current_timestamp()`), so every row in bronze can
# MAGIC be traced back to the file it came from and when it was loaded.

# COMMAND ----------

races_final_df = add_ingestion_metadata(races_df)

# COMMAND ----------

display(races_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.races` table on
# MAGIC every run, consistent with this project's full-refresh design.

# COMMAND ----------

(
    races_final_df
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
# MAGIC read from `races.csv` should land in the bronze table. `FAILFAST` already
# MAGIC guarantees the source read itself is either complete or raises, so a
# MAGIC mismatch here would point to a bug in the write path rather than in the
# MAGIC source file.

# COMMAND ----------

source_row_count = races_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
