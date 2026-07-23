# Databricks notebook source
# MAGIC %md
# MAGIC # Build Results Fact
# MAGIC
# MAGIC Builds `fact_session_results`, the central **fact table** of the gold
# MAGIC layer. Its grain is **one row per driver, per session, per race** - a
# MAGIC "session" being either the race itself or, on the weekends that had one,
# MAGIC the sprint - discriminated by the `session_type` column (`RACE` /
# MAGIC `SPRINT`). Unlike a dimension (a descriptive, slowly-changing entity such
# MAGIC as `dim_drivers` or `dim_races`), a fact table records measurable events:
# MAGIC here, a driver's finishing position and points for a given session.
# MAGIC
# MAGIC `results` and `sprints` are two silver tables with the same business
# MAGIC shape (a driver's outcome in a session) but were kept separate upstream
# MAGIC because a race weekend has at most one sprint and it is scored
# MAGIC differently to the race. Tagging each with a `session_type` literal and
# MAGIC unioning them into a single fact table is the standard pattern for
# MAGIC combining two similar event types into one consistent grain, so
# MAGIC downstream consumers can query "all session results" without caring which
# MAGIC silver table a row originally came from.
# MAGIC
# MAGIC 1. Read silver `results` table
# MAGIC 1. Read silver `sprints` table
# MAGIC 1. Add new column `session_type` with values `RACE` or `SPRINT`
# MAGIC 1. UNION `results` and `sprints`
# MAGIC 1. Derive additional columns
# MAGIC     - is_win -> Indicates that the driver won the race
# MAGIC     - is_podium -> Indicates that the driver scored a podium result (1, 2, 3)
# MAGIC     - has_points -> Indicates that the driver has scored points
# MAGIC 1. Write the transformed data to gold `fact_session_results` table
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Silver Schema
# MAGIC
# MAGIC ![Formula1 Silver Data.png](../../z-course-images/formula1-silver-data-erd.png "Formula1 Silver Data.png")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Gold Schema
# MAGIC
# MAGIC ![Formula1 Gold Data.png](../../z-course-images/formula1-gold-data-erd.png "Formula1 Gold Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

target_table = f"{catalog_name}.{gold_schema}.fact_session_results"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read source tables
# MAGIC - `silver.results`
# MAGIC - `silver.sprints`

# COMMAND ----------

# `race_name`, `race_date`, `ingestion_timestamp`, and `source_file` are
# race/audit metadata that already lives on `dim_races` and are not part of
# the fact grain - they are dropped here so that `results_df` and
# `sprints_df` end up with identical schemas before the union below.
results_df = (
    spark.table(f"{catalog_name}.{silver_schema}.results")
         .withColumn("session_type", F.lit("RACE"))
         .drop("race_name", "race_date", "ingestion_timestamp", "source_file")
)

# COMMAND ----------

# Same treatment as results_df above, tagged SPRINT instead of RACE, so both
# sides of the union below share the exact same columns.
sprints_df = (
    spark.table(f"{catalog_name}.{silver_schema}.sprints")
         .withColumn("session_type", F.lit("SPRINT"))
         .drop("race_name", "race_date", "ingestion_timestamp", "source_file")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - UNION `results` and `sprints`
# MAGIC
# MAGIC `unionByName` matches columns by name rather than by position, so it
# MAGIC fails fast with a clear error if the two sides ever drift out of schema
# MAGIC sync - safer here than a plain positional `union` now that both frames
# MAGIC have been trimmed to the same column set.

# COMMAND ----------

results_sprints_df = results_df.unionByName(sprints_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Add derived columns
# MAGIC 1. is_win -> Indicates that the driver won the race
# MAGIC 1. is_podium -> Indicates that the driver scored a podium result (1, 2, 3)
# MAGIC 1. has_points -> Indicates that the driver has scored points
# MAGIC
# MAGIC These are simple boolean predicates on `final_position` and `points`, and
# MAGIC any BI tool could recompute them on the fly. They are pre-computed here
# MAGIC instead because this is the gold layer: doing the calculation once, in
# MAGIC one place, means every downstream query - including both standings views
# MAGIC in `05-analytics` - can rely on a plain `COUNT_IF(is_win)` /
# MAGIC `COUNT_IF(is_podium)` rather than every report re-deriving the same
# MAGIC "position between 1 and 3" logic (and risking getting it slightly wrong).

# COMMAND ----------

fact_session_results_df = (
    results_sprints_df
        .withColumn("is_win", F.col("final_position") == 1)
        .withColumn("is_podium", F.col("final_position").between(1, 3))
        .withColumn("has_points", F.col("points") > 0)
)

# COMMAND ----------

display(fact_session_results_df.filter("season = 2025"))

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 4 - Write the transformed data to the `gold` `fact_session_results` table
# MAGIC
# MAGIC `overwrite` fully replaces the table on every run - the same full-refresh
# MAGIC strategy used across all gold notebooks in this project (see
# MAGIC `01.Build Races Dimension` for the reasoning). The equivalent notebook in
# MAGIC `05_formula1-project-incremental-load` instead `MERGE`s only the batches
# MAGIC that changed.

# COMMAND ----------

(
    fact_session_results_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))