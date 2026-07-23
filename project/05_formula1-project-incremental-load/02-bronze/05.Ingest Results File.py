# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest results.json file
# MAGIC 1. Read all the files from the results folder using spark dataframe reader API
# MAGIC 1. Define and enforce schema
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC This notebook is parameterized by `p_batch_id`: each batch's raw files
# MAGIC live in their own numbered subfolder under `landing_folder_path`, and
# MAGIC `source_file` below points at the batch's whole `results` folder
# MAGIC rather than a single file, since a batch's results can be split across
# MAGIC multiple JSON files. The write step uses `write_to_bronze`
# MAGIC (`00-common/02.bronze-helpers`), which overwrites only this batch's own
# MAGIC partition of the `results` bronze table via Delta's `replaceWhere` -
# MAGIC re-running this notebook for one batch never touches any other
# MAGIC batch's rows already loaded.

# COMMAND ----------

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/02.bronze-helpers

# COMMAND ----------

# Define source_file and table_name
source_file = f"{landing_folder_path}/{v_batch_id}/results"
table_name = f"{catalog_name}.{bronze_schema}.results"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API

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

# COMMAND ----------

results_final_df = add_ingestion_metadata(results_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table

# COMMAND ----------

write_to_bronze (
    input_df = results_final_df,
    target_table = table_name,
    batch_id = v_batch_id
)

# COMMAND ----------

display(spark.table(table_name))