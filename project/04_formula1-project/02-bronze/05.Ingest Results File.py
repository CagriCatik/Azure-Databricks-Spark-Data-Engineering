# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest results.json file
# MAGIC 1. Read the all the files from the results folder using spark dataframe reader API
# MAGIC 1. Define and enforce schema
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This is a **bronze** notebook: it lands the `results` source into Delta
# MAGIC with full fidelity and minimal transformation - no filtering,
# MAGIC deduplication, or derived columns (e.g. no ranking or points aggregation)
# MAGIC beyond parsing the declared schema. `source_file` points at a **folder**,
# MAGIC not a single file - Spark's file-based readers accept a folder path and
# MAGIC transparently read every file inside it as one logical DataFrame, which is
# MAGIC why `source_file` (added in Step 2, from `_metadata.file_path`) matters:
# MAGIC it is the only way to tell, after the fact, which individual file within
# MAGIC that folder any given row actually came from.
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

# Define source_file and table_name
source_file = f"{landing_folder_path}/results"
table_name = f"{catalog_name}.{bronze_schema}.results"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API
# MAGIC
# MAGIC `results` columns: `date`, `raceName`, `round`, `season`, `url`,
# MAGIC `constructorId`, `driverId`, `grid`, `laps`, `number`, `points`,
# MAGIC `position`, `positionText`, `status` - one row per driver per race result.
# MAGIC `constructorId` and `driverId` are the join keys back to
# MAGIC `formula1.bronze.constructors` and `formula1.bronze.drivers`.
# MAGIC
# MAGIC `position` is nullable by design (not enforced with `nullable=False`
# MAGIC here, but functionally so): a driver who retires or is disqualified has no
# MAGIC finishing position, only a `positionText` such as `"R"` or `"DNF"`. An
# MAGIC explicit schema, rather than `inferSchema`, is what makes this
# MAGIC deliberately-nullable numeric column behave consistently - `inferSchema`
# MAGIC could just as easily infer `position` as a string the moment it samples a
# MAGIC non-numeric value first, silently changing the column's type from what
# MAGIC earlier runs produced.
# MAGIC
# MAGIC `mode('FAILFAST')` raises immediately on any row that does not conform to
# MAGIC the declared schema, instead of silently writing `NULL`s (the default
# MAGIC `PERMISSIVE` mode) or dropping offending rows (`DROPMALFORMED`) - across
# MAGIC potentially many files in this folder, that is what guarantees a bad
# MAGIC record in any single file fails the whole load loudly rather than quietly
# MAGIC shipping a partially-corrupt bronze table.

# COMMAND ----------

# Define the schema
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType, DateType

results_schema = StructType([
    StructField("date", DateType()),
    StructField("raceName", StringType()),
    StructField("round", IntegerType()),
    StructField("season", IntegerType()),
    StructField("url", StringType()),
    StructField("constructorId", StringType()),
    StructField("driverId", StringType()),
    StructField("grid", IntegerType()),
    StructField("laps", IntegerType()),
    StructField("number", IntegerType()),
    StructField("points", FloatType()),
    StructField("position", IntegerType()),
    StructField("positionText", StringType()),
    StructField("status", StringType())
])

# COMMAND ----------

# Read data from the results file
results_df = (
    spark.read
       .format('json')
       .schema(results_schema)
       .option('mode', 'FAILFAST')
       .load(source_file)
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Add Metadata Columns
# MAGIC - Source File
# MAGIC - Ingestion Timestamp
# MAGIC
# MAGIC `add_ingestion_metadata` (from `00-common/02.bronze-helpers`) appends
# MAGIC `source_file` (from Spark's built-in `_metadata.file_path`) and
# MAGIC `ingestion_timestamp` (`current_timestamp()`). Since `results` is read
# MAGIC from a multi-file folder, `source_file` here is what lets you trace any
# MAGIC given row back to the one specific file it came from.

# COMMAND ----------

results_final_df = add_ingestion_metadata(results_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.results` table
# MAGIC on every run, consistent with this project's full-refresh design.

# COMMAND ----------

(
    results_final_df
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
# MAGIC read across every file in the `results` folder should land in the bronze
# MAGIC table. `FAILFAST` already guarantees the source read itself is either
# MAGIC complete or raises, so a mismatch here would point to a bug in the write
# MAGIC path rather than in the source files.

# COMMAND ----------

source_row_count = results_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
