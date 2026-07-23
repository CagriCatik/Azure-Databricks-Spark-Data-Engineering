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
# MAGIC > - **`05.Transform Results Data.py`** (this file) - the default/reference
# MAGIC >   implementation, functionally identical to `(Fully-Chained)` below.
# MAGIC > - **`05.Transform Results Data (Fully-Chained).py`** - the same
# MAGIC >   transformation written as one chained DataFrame expression, for
# MAGIC >   conciseness.
# MAGIC > - **`05.Transform Results Data (Step-by-Step).py`** - the same
# MAGIC >   transformation broken into one named DataFrame per step, useful when
# MAGIC >   debugging a specific stage in isolation.
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
# MAGIC #### Step 1 & 4 - Read bronze `results` table, select only the required columns and standardise column names
# MAGIC
# MAGIC `url` is dropped simply by not selecting it - it carries no analytical value.
# MAGIC The remaining bronze camelCase fields (`constructorId`, `driverId`, `raceName`,
# MAGIC `positionText`, ...) are renamed in the same step to snake_case and to more
# MAGIC descriptive names (`grid` → `grid_position`, `position` → `final_position`,
# MAGIC etc.), matching the column names used for the equivalent fields in the
# MAGIC `sprints` notebook so the two tables can later be combined with
# MAGIC `unionByName` in the gold fact table.

# COMMAND ----------

results_df = (
  spark.table(bronze_table)
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
                "source_file")
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
# MAGIC #### Step 5 & 6 Apply Data Quality Checks
# MAGIC - Filter out rows where `season`, `round`, `constructor_id` or `driver_id` is null (business key validation)
# MAGIC - Remove duplicate records
# MAGIC
# MAGIC `(season, round, constructor_id, driver_id)` together identify a unique
# MAGIC driver/constructor entry within a race - the composite business key the gold
# MAGIC fact table depends on. Rows missing any part of that key can never be joined
# MAGIC or grouped correctly downstream, so they are filtered out here;
# MAGIC `dropDuplicates` on the same columns then collapses any rows re-introduced by
# MAGIC re-running ingestion.

# COMMAND ----------

results_valid_df = (
    results_df
        .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("constructor_id").isNotNull() &
            F.col("driver_id").isNotNull()
        )
        .dropDuplicates(["season", "round", "constructor_id", "driver_id"])
)

# COMMAND ----------

# Sanity check: how many rows the combined null-key filter and de-duplication
# step above removed.
display(results_df.count() - results_valid_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Transform values of column `race_name` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes this free-text display column to Title Case for consistent
# MAGIC presentation in reports and dashboards.

# COMMAND ----------

results_final_df = (
    results_valid_df
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
