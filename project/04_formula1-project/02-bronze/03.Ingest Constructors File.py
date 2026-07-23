# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest constructors.json file
# MAGIC 1. Read the file using spark dataframe reader API
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This is a **bronze** notebook: it lands `constructors.json` into Delta
# MAGIC with full fidelity and minimal transformation - no filtering,
# MAGIC deduplication, or renaming beyond parsing the declared schema.
# MAGIC Constructors is reference/lookup data (one row per team), and this
# MAGIC project (`04_formula1-project`) is a **full-refresh** pipeline: this
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
source_file = f"{landing_folder_path}/constructors.json"
table_name = f"{catalog_name}.{bronze_schema}.constructors"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API
# MAGIC
# MAGIC `constructors.json` columns: `constructorId`, `name`, `nationality`,
# MAGIC `url` - a flat structure, so the schema is expressed as a DDL string
# MAGIC (Spark's shorthand for a `StructType`) rather than a `StructType(...)`
# MAGIC object; both are equivalent and equally explicit.
# MAGIC
# MAGIC As with every other bronze notebook in this project, `inferSchema` is
# MAGIC deliberately not used - an explicit schema keeps this bronze table's
# MAGIC contract stable and reviewable in code, instead of silently changing if
# MAGIC the source JSON's shape or types drift between loads.
# MAGIC
# MAGIC `mode('FAILFAST')` raises immediately on any row that does not conform to
# MAGIC the declared schema, instead of silently writing `NULL`s (the default
# MAGIC `PERMISSIVE` mode) or dropping offending rows (`DROPMALFORMED`) - a loud
# MAGIC failure here is far preferable to quietly corrupting bronze data that
# MAGIC silver notebooks trust as the raw source of truth.

# COMMAND ----------

# Define the schema
constructors_schema = """constructorId STRING,
                         name STRING,
                         nationality STRING,
                         url STRING
                         """

# COMMAND ----------

# Read data from the constructors file
constructors_df = (
    spark.read
       .format('json')
       .schema(constructors_schema)
       .option('mode', 'FAILFAST')
       .load(source_file)
)

# COMMAND ----------

display(constructors_df)

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

constructors_final_df = add_ingestion_metadata(constructors_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table
# MAGIC
# MAGIC `.mode('overwrite')` replaces the entire `formula1.bronze.constructors`
# MAGIC table on every run, consistent with this project's full-refresh design.

# COMMAND ----------

(
    constructors_final_df
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
# MAGIC read from `constructors.json` should land in the bronze table. `FAILFAST`
# MAGIC already guarantees the source read itself is either complete or raises,
# MAGIC so a mismatch here would point to a bug in the write path rather than in
# MAGIC the source file.

# COMMAND ----------

source_row_count = constructors_final_df.count()
bronze_row_count = spark.table(table_name).count()

print(f"Source rows read    : {source_row_count}")
print(f"Bronze rows written : {bronze_row_count}")

assert source_row_count == bronze_row_count, (
    f"Row count mismatch after write to {table_name}: "
    f"read {source_row_count}, found {bronze_row_count}"
)
