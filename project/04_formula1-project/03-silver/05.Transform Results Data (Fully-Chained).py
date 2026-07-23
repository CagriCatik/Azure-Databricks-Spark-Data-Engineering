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
# MAGIC > - **`05.Transform Results Data (Fully-Chained).py`** (this file) - the
# MAGIC >   same transformation as the plain version above, written as one chained
# MAGIC >   DataFrame expression for conciseness.
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
# MAGIC #### Step 1 to 7 - Read , transform, & perform data quality checks
# MAGIC
# MAGIC The same steps as the reference notebook, chained into a single expression:
# MAGIC select only the analytics-relevant columns (dropping `url`), rename to
# MAGIC snake_case/more meaningful names, filter out rows with a null business key
# MAGIC (`season`, `round`, `constructor_id`, `driver_id`), drop duplicate rows on
# MAGIC that same composite key, and title-case `race_name`. See the
# MAGIC `(Step-by-Step)` notebook if you want to inspect the DataFrame after any
# MAGIC individual stage instead.

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
       .filter(
            F.col("season").isNotNull() &
            F.col("round").isNotNull() &
            F.col("constructor_id").isNotNull() &
            F.col("driver_id").isNotNull()
        )
       .dropDuplicates(["season", "round", "constructor_id", "driver_id"])
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
    results_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))
