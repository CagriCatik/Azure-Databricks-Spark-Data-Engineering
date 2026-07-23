# Databricks notebook source
# MAGIC %md
# MAGIC # Ingest sprints.json file
# MAGIC 1. Read all the files from the sprints folder using spark dataframe reader API
# MAGIC 1. Define and enforce schema
# MAGIC 1. Add Metadata Columns
# MAGIC     - Source File
# MAGIC     - Ingestion Timestamp
# MAGIC 1. Write to bronze delta table
# MAGIC
# MAGIC > Note: JSON is in multi line format
# MAGIC
# MAGIC This notebook is parameterized by `p_batch_id`: each batch's raw files
# MAGIC live in their own numbered subfolder under `landing_folder_path`, and
# MAGIC `source_file` below points at the batch's whole `sprints` folder
# MAGIC rather than a single file, since a batch's sprint results can be split
# MAGIC across multiple multi-line JSON files. The write step uses
# MAGIC `write_to_bronze` (`00-common/02.bronze-helpers`), which overwrites
# MAGIC only this batch's own partition of the `sprints` bronze table via
# MAGIC Delta's `replaceWhere` - re-running this notebook for one batch never
# MAGIC touches any other batch's rows already loaded.

# COMMAND ----------

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/02.bronze-helpers

# COMMAND ----------

# Define source_file and table_name
source_file = f"{landing_folder_path}/{v_batch_id}/sprints"
table_name = f"{catalog_name}.{bronze_schema}.sprints"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read the JSON file using the dataframe reader API

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

# COMMAND ----------

sprints_final_df = add_ingestion_metadata(sprints_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write to bronze delta table

# COMMAND ----------

write_to_bronze (
    input_df = sprints_final_df,
    target_table = table_name,
    batch_id = v_batch_id
)

# COMMAND ----------

display(spark.table(table_name))