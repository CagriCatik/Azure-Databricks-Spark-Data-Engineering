# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Races Data
# MAGIC
# MAGIC 1. Read bronze `races` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`raceName` → `race_name`, `circuitId` → `circuit_id`)
# MAGIC 1. Rename columns to make them more meaningful (`date` → `race_date`)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of column `race_name` to Title Case
# MAGIC 1. Write the transformed data to silver `races` table
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
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# p_batch_id is passed in by the orchestrating job and identifies which bronze batch this
# run should process - the same batch_id the bronze notebook used to tag the rows it wrote.
dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/03.silver-helpers

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.races"
silver_table = f"{catalog_name}.{silver_schema}.races"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `races` table

# COMMAND ----------

# Bronze writes are batch-scoped `replaceWhere` overwrites, so the bronze table keeps every
# batch ever ingested. Filtering on batch_id here means we only transform the rows that
# belong to the current batch, not the whole race history on every run.
races_df = (
    spark.table(bronze_table)
         .filter((F.col("batch_id") == v_batch_id))
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)

# COMMAND ----------

races_selected_df = races_df.select(
    F.col("season"),
    F.col("round"),
    F.col("raceName"),
    F.col("date"),
    F.col("circuitId"),
    F.col("ingestion_timestamp"),
    F.col("source_file"),
    F.col("batch_id")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`circuitId` → `circuit_id`, `raceName` → `race_name`)
# MAGIC - Rename columns to make them more meaningful (`date` → `race_date`)

# COMMAND ----------

races_renamed_df = (
    races_selected_df
        .withColumnsRenamed({
            "circuitId": "circuit_id",
            "raceName": "race_name",
            "date": "race_date"
        })
)

# COMMAND ----------

display(races_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 - Remove duplicate records

# COMMAND ----------

# season + round is the business key a race is uniquely identified by (and the key we merge
# on in Step 7), so dedup on that composite key rather than a whole-row .distinct().
races_distinct_df = races_renamed_df.dropDuplicates(["season","round"])

# COMMAND ----------

display(races_distinct_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Transform values of column `race_name` to Title Case

# COMMAND ----------

races_final_df = (
    races_distinct_df
        .withColumn('race_name', F.initcap(F.col("race_name")))
)

# COMMAND ----------

display(races_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Write the transformed data to silver `races` table

# COMMAND ----------

# write_to_silver (00-common/03.silver-helpers) creates the silver table on the very first
# run; on every subsequent run it performs a Delta MERGE keyed on merge_condition, the
# (season, round) composite business key:
#   - whenMatchedUpdate only fires when s.batch_id >= t.batch_id, so a re-run of an older
#     or already-superseded batch can never overwrite a row a newer batch has updated
#   - whenNotMatchedInsertAll inserts races that are new to silver
#   - created_timestamp is set once by the helper and is deliberately left out of
#     columns_to_update, so a matched-row update never disturbs the original insert time;
#     updated_timestamp, by contrast, is refreshed by the helper on every merge
write_to_silver(
    input_df=races_final_df,
    target_table=silver_table,
    merge_condition="t.season = s.season AND t.round = s.round",
    columns_to_update=[
        "race_name",
        "race_date",
        "circuit_id",
        "ingestion_timestamp",
        "source_file",
        "batch_id"
    ]
)

# COMMAND ----------

display(spark.table(silver_table))
