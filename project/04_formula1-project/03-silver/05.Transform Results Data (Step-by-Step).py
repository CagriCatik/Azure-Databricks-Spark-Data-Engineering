# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Results Data
# MAGIC
# MAGIC 1. Read bronze `results` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`constructorId` → `constructor_id`, `driverId` → `driver_id`, `raceName` → `race_name`, `positionText` → `final_position_text`)
# MAGIC 1. Rename columns to make them more meaningful (`date` → `race_date`, `grid` → `grid_position`, `laps` → `completed_laps`, `number` → `car_number`, `position` → `final_position`)
# MAGIC 1. Filter out rows where `season`, `round`, `constructor_id` or `driver_id` is null (business key validation)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of column `race_name` to Title Case
# MAGIC 1. Write the transformed data to silver `results` table
# MAGIC
# MAGIC > **Three Results notebooks, one transformation.** This folder has three
# MAGIC > notebooks that all build the same silver `results` table with identical
# MAGIC > logic, kept side by side deliberately for teaching purposes:
# MAGIC >
# MAGIC > - **`05.Transform Results Data.py`** - the default/reference
# MAGIC >   implementation.
# MAGIC > - **`05.Transform Results Data (Fully-Chained).py`** - the same
# MAGIC >   transformation written as one chained DataFrame expression, for
# MAGIC >   conciseness.
# MAGIC > - **`05.Transform Results Data (Step-by-Step).py`** (this file) - the
# MAGIC >   same transformation broken into one named DataFrame per step
# MAGIC >   (`results_selected_df` → `results_renamed_df` → `results_valid_df` →
# MAGIC >   `results_distinct_df` → `results_final_df`), useful when debugging a
# MAGIC >   specific stage in isolation. Includes two extra sanity-check cells that
# MAGIC >   print how many rows the null-key filter and de-duplication steps each
# MAGIC >   remove.
# MAGIC
# MAGIC This notebook builds the silver `results` table: bronze data cleaned, renamed,
# MAGIC filtered for referential integrity, and de-duplicated on
# MAGIC `(season, round, constructor_id, driver_id)`. It is unioned with silver
# MAGIC `sprints` in the gold `fact_session_results` table (see
# MAGIC `04-gold/04.Build Results Fact`), tagged there with `session_type = 'RACE'` -
# MAGIC so the columns produced here (`final_position`, `points`, `constructor_id`,
# MAGIC `driver_id`, `season`, `round`, ...) must line up name-for-name with the
# MAGIC `sprints` notebook. As with the rest of this project variant, the final write
# MAGIC is a full overwrite - no incremental/batch tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Bronze Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.results"
silver_table = f"{catalog_name}.{silver_schema}.results"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `results` table

# COMMAND ----------

results_df = spark.table(bronze_table)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)
# MAGIC
# MAGIC `url` is a link back to the source website with no analytical value - it is
# MAGIC dropped simply by not selecting it here.

# COMMAND ----------

results_selected_df = (
  results_df.select("season",
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
                    "source_file")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`constructorId` → `constructor_id`, `driverId` → `driver_id`, `raceName` → `race_name`, `positionText` → `final_position_text`)
# MAGIC - Rename columns to make them more meaningful (`date` → `race_date`, `grid` → `grid_position`, `laps` → `completed_laps`, `number` → `car_number`, `position` → `final_position`)
# MAGIC
# MAGIC Bronze mirrors the source API's camelCase fields as-is; silver renames them to
# MAGIC snake_case, the convention expected by Spark SQL, Delta table columns, and
# MAGIC downstream BI tools. Columns are renamed to their final, more descriptive
# MAGIC names in this same step, matching the column names used for the equivalent
# MAGIC fields in the `sprints` notebook so the two tables can later be combined with
# MAGIC `unionByName` in the gold fact table.

# COMMAND ----------

results_renamed_df = (
    results_selected_df
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
# MAGIC #### Step 5 - Filter out rows where `season`, `round`, `constructor_id` or `driver_id` is null (business key validation)
# MAGIC
# MAGIC `(season, round, constructor_id, driver_id)` together identify a unique
# MAGIC driver/constructor entry within a race - the composite business key the gold
# MAGIC fact table depends on. A row missing any part of that key can never be joined
# MAGIC or grouped correctly downstream, so it is dropped here.

# COMMAND ----------

results_valid_df = (
    results_renamed_df
        .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("constructor_id").isNotNull() &
            F.col("driver_id").isNotNull()
        )
)

# COMMAND ----------

# Sanity check: how many rows were dropped for having a null business key
# (season, round, constructor_id, or driver_id).
display(results_renamed_df.count() - results_valid_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Remove duplicate records
# MAGIC
# MAGIC Re-running bronze ingestion against the same source file can re-introduce
# MAGIC exact-duplicate rows. `dropDuplicates` is scoped to the composite business key
# MAGIC rather than a plain `.distinct()`, which would only catch rows that match on
# MAGIC every single column.

# COMMAND ----------

results_distinct_df = results_valid_df.dropDuplicates(["season", "round", "constructor_id", "driver_id"])

# COMMAND ----------

# Sanity check: how many duplicate rows were collapsed by dropDuplicates.
display(results_valid_df.count() - results_distinct_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Transform values of column `race_name` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes this free-text display column to Title Case for consistent
# MAGIC presentation in reports and dashboards.

# COMMAND ----------

results_final_df = (
    results_distinct_df
        .withColumn('race_name', F.initcap(F.col("race_name")))
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 8 - Write the transformed data to silver `results` table
# MAGIC
# MAGIC `mode('overwrite')` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project variant (see
# MAGIC `05_formula1-project-incremental-load` for the MERGE/batch-tracking variant).

# COMMAND ----------

(
    results_final_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))
