# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest drivers.json file
# MAGIC 1. Read the file using spark dataframe reader API
# MAGIC 1. Define and enforce schema (preserve the nested structure)
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This is a **bronze** notebook: it lands `drivers.json` into Delta with
# MAGIC full fidelity and minimal transformation - the nested `name` struct is
# MAGIC preserved as-is rather than flattened, since flattening (e.g. into
# MAGIC `first_name`/`last_name`) is a silver-layer concern, not a bronze one.
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
source_file = f"{landing_folder_path}/drivers.json"
table_name = f"{catalog_name}.{bronze_schema}.drivers"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API
# MAGIC
# MAGIC `drivers.json` columns: `driverId`, `name` (nested struct with
# MAGIC `givenName` and `familyName`), `dateOfBirth`, `nationality`, `url`.
# MAGIC
# MAGIC Unlike the flat sources ingested elsewhere in this project, `drivers.json`
# MAGIC has a nested field, which is exactly why an explicit, nested `StructType`
# MAGIC matters even more here than usual: `inferSchema` on nested JSON can widen
# MAGIC or reshape struct fields unpredictably depending on which records happen
# MAGIC to be sampled, whereas the `StructType` below pins down `name.givenName`
# MAGIC and `name.familyName` precisely and keeps the struct's shape stable across
# MAGIC runs.
# MAGIC
# MAGIC `mode('FAILFAST')` raises immediately on any row that does not conform to
# MAGIC the declared schema, instead of silently writing `NULL`s (the default
# MAGIC `PERMISSIVE` mode) or dropping offending rows (`DROPMALFORMED`) - a loud
# MAGIC failure here is far preferable to quietly corrupting bronze data that
# MAGIC silver notebooks trust as the raw source of truth.

# COMMAND ----------

# Define the schema
from pyspark.sql.types import StructType, StructField, StringType, DateType

name_schema = StructType([
    StructField('givenName', StringType()),
    StructField('familyName', StringType())
])

drivers_schema = StructType([
    StructField('driverId', StringType()),
    StructField('name', name_schema),
    StructField('dateOfBirth', DateType()),
    StructField('nationality', StringType()),
    StructField('url', StringType())
])

# COMMAND ----------

# Read data from the drivers file
drivers_df = (
    spark.read
       .format('json')
       .schema(drivers_schema)
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
# MAGIC `ingestion_timestamp` (`current_timestamp()`), so every row in bronze can
# MAGIC be traced back to the file it came from and when it was loaded.

# COMMAND ----------

drivers_final_df = add_ingestion_metadata(drivers_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.drivers` table
# MAGIC on every run, consistent with this project's full-refresh design. The
# MAGIC nested `name` struct is written to Delta as-is - Delta natively supports
# MAGIC struct columns, so no flattening is needed just to persist the data.

# COMMAND ----------

(
    drivers_final_df
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
# MAGIC read from `drivers.json` should land in the bronze table. `FAILFAST`
# MAGIC already guarantees the source read itself is either complete or raises,
# MAGIC so a mismatch here would point to a bug in the write path rather than in
# MAGIC the source file.

# COMMAND ----------

source_row_count = drivers_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
