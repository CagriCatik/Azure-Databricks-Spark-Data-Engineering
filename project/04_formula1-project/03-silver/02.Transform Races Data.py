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
# MAGIC This notebook builds the silver `races` table: one row per season/round, joined
# MAGIC downstream to `circuits` by `circuit_id` to build the gold `dim_races` table (see
# MAGIC `04-gold/01.Build Races Dimension`). Unlike some of the other silver notebooks in
# MAGIC this folder, there is no explicit null-business-key filter step here - only
# MAGIC de-duplication on `(season, round)`. As with the rest of this project variant,
# MAGIC the final write is a full overwrite - no incremental/batch tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.races"
silver_table = f"{catalog_name}.{silver_schema}.races"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `races` table

# COMMAND ----------

races_df = spark.table(bronze_table)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)
# MAGIC
# MAGIC `url` is a link back to the source website with no analytical value, so it is
# MAGIC dropped simply by not selecting it here.

# COMMAND ----------

races_selected_df = races_df.select(
    F.col("season"),
    F.col("round"),
    F.col("raceName"),
    F.col("date"),
    F.col("circuitId"),
    F.col("ingestion_timestamp"),
    F.col("source_file")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`circuitId` → `circuit_id`, `raceName` → `race_name`)
# MAGIC - Rename columns to make them more meaningful (`date` → `race_date`)
# MAGIC
# MAGIC Bronze mirrors the source API's camelCase fields as-is; silver renames them to
# MAGIC snake_case, the convention expected by Spark SQL, Delta table columns, and
# MAGIC downstream BI tools. `date` is also renamed to the more descriptive `race_date`
# MAGIC to avoid ambiguity once this table is joined against other date-bearing tables
# MAGIC in gold.

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
# MAGIC
# MAGIC `(season, round)` uniquely identifies a race - one Grand Prix per round per
# MAGIC season - so `dropDuplicates` is scoped to those two columns to collapse any
# MAGIC re-ingested duplicate rows down to a single record per race.

# COMMAND ----------

races_distinct_df = races_renamed_df.dropDuplicates(["season", "round"])

# COMMAND ----------

display(races_distinct_df)

# COMMAND ----------

# Sanity check: how many duplicate rows were collapsed by dropDuplicates.
display(races_renamed_df.count() - races_distinct_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Transform values of column `race_name` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes this free-text display column to Title Case for consistent
# MAGIC presentation in reports and dashboards.

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
# MAGIC
# MAGIC `mode('overwrite')` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project variant (see
# MAGIC `05_formula1-project-incremental-load` for the MERGE/batch-tracking variant).

# COMMAND ----------

(
    races_final_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))
