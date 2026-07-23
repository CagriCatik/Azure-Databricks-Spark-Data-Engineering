# Databricks notebook source
# MAGIC %md
# MAGIC # Build Results Fact
# MAGIC
# MAGIC Builds the gold `fact_session_results` fact table. Grain: one row per
# MAGIC (`season`, `round`, `constructor_id`, `driver_id`, `session_type`) — i.e. one
# MAGIC row per driver's result in a single race or sprint session. `session_type`
# MAGIC (`RACE` / `SPRINT`) is a degenerate dimension that lets the same physical
# MAGIC race weekend contribute two independent result rows for a driver.
# MAGIC
# MAGIC 1. Read silver `results` table
# MAGIC 1. Read silver `sprints` table
# MAGIC 1. Add new column `session_type` with values `RACE` or `SPRINT`
# MAGIC 1. UNION `results` and `sprints`
# MAGIC 1. Derive additional columns
# MAGIC     - is_win -> Indicates that the driver won the session
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

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/04.gold-helpers

# COMMAND ----------

target_table = f"{catalog_name}.{gold_schema}.fact_session_results"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read source tables
# MAGIC - `silver.results`
# MAGIC - `silver.sprints`
# MAGIC
# MAGIC Both reads are filtered to `batch_id = v_batch_id`, then each drops the
# MAGIC silver-only lineage columns (`race_name`, `race_date`, `ingestion_timestamp`,
# MAGIC `source_file`, `batch_id`, `created_timestamp`, `updated_timestamp`) — none
# MAGIC of these belong on the fact table, which is keyed by
# MAGIC `season, round, constructor_id, driver_id, session_type` and gets its own
# MAGIC `created_timestamp` / `updated_timestamp` from `write_to_gold`.
# MAGIC
# MAGIC > **Known limitation — no batch-order guard at the gold layer.**
# MAGIC > `write_to_silver` protects against an out-of-order rerun with
# MAGIC > `whenMatchedUpdate(condition="s.batch_id >= t.batch_id", ...)`, so a stale
# MAGIC > batch replayed after a newer one already updated silver cannot overwrite
# MAGIC > it. `write_to_gold` has no equivalent guard — and it *can't*, because
# MAGIC > `batch_id` is dropped from `results_df` / `sprints_df` right here, before
# MAGIC > the data ever reaches `write_to_gold`. There is no `batch_id` column left
# MAGIC > on either side of that merge for a condition to reference.
# MAGIC >
# MAGIC > In practice this means `fact_session_results` is **last-write-wins per
# MAGIC > business key, regardless of which batch ran last**: if an older batch is
# MAGIC > reprocessed after a newer batch has already merged into gold, the older
# MAGIC > batch's values will silently overwrite the newer ones — nothing in this
# MAGIC > notebook or in `write_to_gold` detects or prevents that.
# MAGIC >
# MAGIC > Fixing this properly would mean carrying `batch_id` through from silver
# MAGIC > into this gold table and adding the same `s.batch_id >= t.batch_id` guard
# MAGIC > used in `write_to_silver`. That is a schema and shared-helper change and is
# MAGIC > out of scope for this notebook, so it is documented here rather than
# MAGIC > silently patched.

# COMMAND ----------

results_df = (
    spark.table(f"{catalog_name}.{silver_schema}.results")
         .filter(F.col("batch_id") == v_batch_id)
         .withColumn("session_type", F.lit("RACE"))
         .drop("race_name", "race_date", "ingestion_timestamp", "source_file", "batch_id", "created_timestamp", "updated_timestamp")
)

# COMMAND ----------

sprints_df = (
    spark.table(f"{catalog_name}.{silver_schema}.sprints")
         .filter(F.col("batch_id") == v_batch_id)
         .withColumn("session_type", F.lit("SPRINT"))
         .drop("race_name", "race_date", "ingestion_timestamp", "source_file", "batch_id", "created_timestamp", "updated_timestamp")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - UNION `results` and `sprints`

# COMMAND ----------

results_sprints_df = results_df.unionByName(sprints_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Add derived columns
# MAGIC 1. is_win -> Indicates that the driver won the session
# MAGIC 1. is_podium -> Indicates that the driver scored a podium result (1, 2, 3)
# MAGIC 1. has_points -> Indicates that the driver has scored points
# MAGIC
# MAGIC Pre-computing these as boolean measures lets downstream consumers (e.g. the
# MAGIC standings views in `05-analytics`) aggregate with a simple `COUNT_IF`
# MAGIC instead of re-deriving win/podium logic from `final_position` each time.

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
# MAGIC Merges on the full business key (`season`, `round`, `constructor_id`,
# MAGIC `driver_id`, `session_type`) — see the Step 1 note above regarding the
# MAGIC absence of a batch-order guard on this particular merge.

# COMMAND ----------

write_to_gold(
    input_df=fact_session_results_df,
    target_table=target_table,
    merge_condition="""
        t.season = s.season
        AND t.round = s.round
        AND t.constructor_id = s.constructor_id
        AND t.driver_id = s.driver_id
        AND t.session_type = s.session_type
    """,
    columns_to_update=[
        "grid_position",
        "completed_laps",
        "car_number",
        "points",
        "final_position",
        "final_position_text",
        "status",
        "is_win",
        "is_podium",
        "has_points"
    ]
)

# COMMAND ----------

display(spark.table(target_table))