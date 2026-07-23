# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest sprints.json file
# MAGIC 1. Read the all the files from the sprints folder using spark dataframe reader API
# MAGIC 1. Define and enforce schema
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC > Note: JSON is in multi line format
# MAGIC
# MAGIC This is a **bronze** notebook: it lands the `sprints` source into Delta
# MAGIC with full fidelity and minimal transformation - no filtering,
# MAGIC deduplication, or derived columns beyond parsing the declared schema.
# MAGIC `source_file` points at a **folder**, not a single file - Spark's
# MAGIC file-based readers accept a folder path and transparently read every file
# MAGIC inside it as one logical DataFrame, which is why `source_file` (added in
# MAGIC Step 2, from `_metadata.file_path`) matters: it is the only way to tell,
# MAGIC after the fact, which individual file within that folder any given row
# MAGIC actually came from.
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
source_file = f"{landing_folder_path}/sprints"
table_name = f"{catalog_name}.{bronze_schema}.sprints"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API
# MAGIC
# MAGIC `sprints` columns: `date`, `raceName`, `round`, `season`, `url`,
# MAGIC `constructorId`, `driverId`, `grid`, `laps`, `number`, `points`,
# MAGIC `position`, `positionText`, `status` - the same shape as
# MAGIC `formula1.bronze.results`, since a sprint result is structurally the same
# MAGIC kind of record as a race result.
# MAGIC
# MAGIC Note that `date` is typed `StringType` here, whereas the equivalent column
# MAGIC in `05.Ingest Results File.py` is typed `DateType`. That is worth flagging
# MAGIC for review if the two sources are ever expected to share a schema or be
# MAGIC unioned - it is left as-is here rather than changed, since silently
# MAGIC "fixing" a bronze schema without checking the actual source file's date
# MAGIC format first (and confirming with FAILFAST that it still parses) risks
# MAGIC turning a working load into a failing one.
# MAGIC
# MAGIC As with every other bronze notebook in this project, `inferSchema` is
# MAGIC deliberately not used - an explicit schema keeps this bronze table's
# MAGIC contract stable and reviewable in code, instead of implicit and dependent
# MAGIC on whatever Spark happens to sample from the files in this folder.
# MAGIC
# MAGIC `mode('FAILFAST')` raises immediately on any row that does not conform to
# MAGIC the declared schema, instead of silently writing `NULL`s (the default
# MAGIC `PERMISSIVE` mode) or dropping offending rows (`DROPMALFORMED`) - across
# MAGIC potentially many files in this folder, that is what guarantees a bad
# MAGIC record in any single file fails the whole load loudly rather than quietly
# MAGIC shipping a partially-corrupt bronze table. `multiLine` is required here
# MAGIC because the sprint JSON files are formatted as pretty-printed, multi-line
# MAGIC JSON rather than one compact JSON object per line.

# COMMAND ----------

# Define the schema
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType, DateType

sprints_schema = StructType([
    StructField("date", StringType()),
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

# Read data from the sprints file
sprints_df = (
    spark.read
       .format('json')
       .schema(sprints_schema)
       .option('mode', 'FAILFAST')
       .option('multiLine', True)
       .load(source_file)
)

# COMMAND ----------

display(sprints_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Add Metadata Columns
# MAGIC - Source File
# MAGIC - Ingestion Timestamp
# MAGIC
# MAGIC `add_ingestion_metadata` (from `00-common/02.bronze-helpers`) appends
# MAGIC `source_file` (from Spark's built-in `_metadata.file_path`) and
# MAGIC `ingestion_timestamp` (`current_timestamp()`). Since `sprints` is read
# MAGIC from a multi-file folder, `source_file` here is what lets you trace any
# MAGIC given row back to the one specific file it came from.

# COMMAND ----------

sprints_final_df = add_ingestion_metadata(sprints_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.sprints` table
# MAGIC on every run, consistent with this project's full-refresh design.

# COMMAND ----------

(
    sprints_final_df
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
# MAGIC read across every file in the `sprints` folder should land in the bronze
# MAGIC table. `FAILFAST` already guarantees the source read itself is either
# MAGIC complete or raises, so a mismatch here would point to a bug in the write
# MAGIC path rather than in the source files.

# COMMAND ----------

source_row_count = sprints_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
