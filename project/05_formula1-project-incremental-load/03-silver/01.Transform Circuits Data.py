# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Circuits Data
# MAGIC
# MAGIC 1. Read bronze `circuits` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`circuitId` → `circuit_id`, `circuitName` → `circuit_name`)
# MAGIC 1. Rename columns to make them more meaningful (`lat` → `latitude`, `long` → `longitude`)
# MAGIC 1. Filter out rows where `circuit_id` is null (business key validation)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of columns `circuit_name` and `locality` to Title Case
# MAGIC 1. Write the transformed data to silver `circuits` table
# MAGIC
# MAGIC > Below changes are required to implement Incremental Load Processing
# MAGIC 1. Accept batch_id as a parameter to the notebook
# MAGIC 1. Process data for only the batch_id being passed in (i.e., filter reading from bronze using the batch_id)
# MAGIC 1. Add created_timestamp, updated_timestamp and batch_id to the silver table.
# MAGIC 1. Merge the processed data to the silver table
# MAGIC     - created_timestamp should only be populated at the time of inserting/ creating the record. It should not be updated during the merge update.
# MAGIC     - Ensure that we are not overwriting the data in silver table by older bronze data (re-run scenario)

# COMMAND ----------

# MAGIC %md
# MAGIC ![incremental-data-processing-medallion.png](../../z-course-images/incremental-data-processing-medallion.png "Incremental Data Processing")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Entity Relationship Diagram - Formula1 Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# p_batch_id is passed in by the orchestrating job (see 06-orchestration) and identifies
# which bronze batch this run should process - the same batch_id the bronze notebook used
# to tag the rows it wrote.
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/03.silver-helpers

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.circuits"
silver_table = f"{catalog_name}.{silver_schema}.circuits"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `circuits` table

# COMMAND ----------

# Bronze writes are batch-scoped `replaceWhere` overwrites, so the bronze table always
# accumulates every batch ever ingested. Filtering on batch_id here is what makes this an
# incremental read: we only process the rows belonging to the current batch instead of
# re-scanning and re-transforming the full history of circuits on every run.
circuits_df = (
    spark.table(bronze_table).filter((F.col("batch_id")== v_batch_id ))
    )

# COMMAND ----------

display(circuits_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)

# COMMAND ----------

circuits_selected_df = circuits_df.select(
    F.col("circuitId"),
    F.col("circuitName"),
    F.col("lat"),
    F.col("long"),
    F.col("locality"),
    F.col("country"),
    F.col("ingestion_timestamp"),
    F.col("source_file"),
    F.col("batch_id")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`circuitId` → `circuit_id`, `circuitName` → `circuit_name`)
# MAGIC - Rename columns to make them more meaningful (`lat` → `latitude`, `long` → `longitude`)

# COMMAND ----------

circuits_renamed_df = (
    circuits_selected_df
        .withColumnsRenamed({
            "circuitId": "circuit_id",
            "circuitName": "circuit_name",
            "lat": "latitude",
            "long": "longitude"
        })
)

# COMMAND ----------

display(circuits_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 - Filter out rows where circuit_id is null (business key validation)

# COMMAND ----------

# circuit_id is the business key we merge on in Step 8 - a null value would mean the row
# can never be matched to (or safely inserted as) a distinct silver record, so it is
# dropped here rather than allowed to reach the merge.
circuits_valid_df = circuits_renamed_df.filter(
    F.col("circuit_id").isNotNull()
)

# COMMAND ----------

display(circuits_valid_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Remove duplicate records

# COMMAND ----------

# Dedup on the business key (circuit_id) rather than a whole-row .distinct(): the goal is
# exactly one row per circuit_id going into the merge, even if this batch happens to carry
# more than one bronze record for the same circuit with differing non-key column values.
circuits_distinct_df = circuits_valid_df.dropDuplicates(["circuit_id"])

# COMMAND ----------

display(circuits_distinct_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Transform values of columns `circuit_name` and `locality` to Title Case

# COMMAND ----------

circuits_final_df = (
    circuits_distinct_df
        .withColumn('circuit_name', F.initcap(F.col("circuit_name")))
        .withColumn('locality', F.initcap(F.col("locality")))
)

# COMMAND ----------

display(circuits_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 8 - Write the transformed data to silver `circuits` table

# COMMAND ----------

# write_to_silver (00-common/03.silver-helpers) creates the silver table on the very first
# run; on every subsequent run it performs a Delta MERGE keyed on merge_condition (the
# circuit_id business key):
#   - whenMatchedUpdate only fires when s.batch_id >= t.batch_id, so a re-run of an older
#     or already-superseded batch can never overwrite a row that a newer batch has updated
#   - whenNotMatchedInsertAll inserts circuits that are new to silver
#   - created_timestamp is set once by the helper and is deliberately left out of
#     columns_to_update, so a matched-row update never disturbs the original insert time;
#     updated_timestamp, by contrast, is refreshed by the helper on every merge
write_to_silver(
    input_df=circuits_final_df,
    target_table=silver_table,
    merge_condition="t.circuit_id = s.circuit_id",
    columns_to_update=[
        "circuit_name",
        "latitude",
        "longitude",
        "locality",
        "country",
        "ingestion_timestamp",
        "source_file",
        "batch_id"
    ]
)

# COMMAND ----------

display(spark.table(silver_table))
