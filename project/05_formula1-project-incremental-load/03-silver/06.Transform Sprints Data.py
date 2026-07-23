# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Sprints Data
# MAGIC 1. Read bronze `sprints` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`constructorId` → `constructor_id`, `driverId` → `driver_id`, `raceName` → `race_name`, `positionText` → `finish_position_text`)
# MAGIC 1. Rename columns to make them more meaningful (`date` → `race_date`, `grid` → `grid_position`, `laps` → `completed_laps`, `number` → `car_number`, `position` → `finish_position`)
# MAGIC 1. Filter out rows where `season`, `round`, `constructor_id` or `driver_id` is null (business key validation)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of column `race_name` to Title Case
# MAGIC 1. Write the transformed data to silver `sprints` table
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
# MAGIC #### Entity Relationship Diagram - Formula1 Bronze Schema
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

bronze_table = f"{catalog_name}.{bronze_schema}.sprints"
silver_table = f"{catalog_name}.{silver_schema}.sprints"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 to 4 Read Source Data, Select required columns & Standardise column names

# COMMAND ----------

# Bronze writes are batch-scoped `replaceWhere` overwrites, so the bronze table keeps every
# batch ever ingested. Filtering on batch_id here means we only transform the rows that
# belong to the current batch, not the whole sprints table on every run.
sprints_df = (
  spark.table(bronze_table)
       .filter((F.col("batch_id") == v_batch_id))
       .select("season",
              "round",
              "constructorId",
              "driverId",
              "date",
              "raceName",
              "grid",
              "laps",
              "number",
              "points",
              "position",
              "positionText",
              "status",
              "ingestion_timestamp",
              "source_file",
              "batch_id")
       .withColumnsRenamed({
            "constructorId": "constructor_id",
            "driverId": "driver_id",
            "raceName": "race_name",
            "date": "race_date",
            "grid": "grid_position",
            "laps": "completed_laps",
            "number": "car_number",
            "position": "final_position",
            "positionText": "final_position_text"
        })
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 & 6 Data Quality Checks
# MAGIC - Filter out rows where `season`, `round`, `constructor_id` or `driver_id` is null (business key validation)
# MAGIC - Remove duplicate records

# COMMAND ----------

# (season, round, constructor_id, driver_id) is the composite business key we merge on in
# Step 8 - one row per sprint entry per constructor/driver pairing. Nulls in any part of
# that key are dropped (they could never be matched or safely inserted), and dropDuplicates
# collapses any repeats of the same key within this batch to a single row.
sprints_valid_df = (
    sprints_df
        .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("constructor_id").isNotNull() &
            F.col("driver_id").isNotNull()
        )
        .dropDuplicates(["season", "round", "constructor_id", "driver_id"])
)

# COMMAND ----------

display(sprints_df.count() - sprints_valid_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Transform values of column `race_name` to Title Case

# COMMAND ----------

sprints_final_df = (
    sprints_valid_df
        .withColumn('race_name', F.initcap(F.col("race_name")))
)

# COMMAND ----------

display(sprints_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 8 - Write the transformed data to silver `sprints` table

# COMMAND ----------

# write_to_silver (00-common/03.silver-helpers) creates the silver table on the very first
# run; on every subsequent run it performs a Delta MERGE keyed on merge_condition, the
# (season, round, constructor_id, driver_id) composite business key:
#   - whenMatchedUpdate only fires when s.batch_id >= t.batch_id, so a re-run of an older
#     or already-superseded batch can never overwrite a row a newer batch has updated
#   - whenNotMatchedInsertAll inserts sprint result rows that are new to silver
#   - created_timestamp is set once by the helper and is deliberately left out of
#     columns_to_update, so a matched-row update never disturbs the original insert time;
#     updated_timestamp, by contrast, is refreshed by the helper on every merge
write_to_silver(
    input_df=sprints_final_df,
    target_table=silver_table,
    merge_condition="t.season = s.season AND t.round = s.round AND t.constructor_id = s.constructor_id AND t.driver_id = s.driver_id",
    columns_to_update=[
        "race_name",
        "race_date",
        "grid_position",
        "completed_laps",
        "car_number",
        "points",
        "final_position",
        "final_position_text",
        "status",
        "ingestion_timestamp",
        "source_file",
        "batch_id"
    ]
)

# COMMAND ----------

display(spark.table(silver_table))
