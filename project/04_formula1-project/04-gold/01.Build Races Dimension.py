# Databricks notebook source
# MAGIC %md
# MAGIC # Build Races Dimension
# MAGIC
# MAGIC Builds the `dim_races` dimension: one row per race (`season` + `round`),
# MAGIC enriched with the circuit it was held at. A **dimension** describes a
# MAGIC business entity - "which race, at which track, on which date" - as
# MAGIC opposed to a **fact table**, which records measurable events (see
# MAGIC `04.Build Results Fact` for the fact side of this model). Race and
# MAGIC circuit are separate silver entities linked by `circuit_id`;
# MAGIC denormalizing them here means every downstream report gets circuit
# MAGIC details for free, without repeating the join.
# MAGIC
# MAGIC 1. Read silver `races` table
# MAGIC 1. Read silver `circuits` table
# MAGIC 1. Join the data from `races` with `circuits` using `circuit_id`
# MAGIC 1. Select the required columns
# MAGIC     - races.season 
# MAGIC     - races.round 
# MAGIC     - races.race_name 
# MAGIC     - races.race_date 
# MAGIC     - circuits.circuit_name 
# MAGIC     - circuits.locality 
# MAGIC     - circuits.country
# MAGIC 1. Write the transformed data to gold `dim_races` table
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

from pyspark.sql import functions as F

# COMMAND ----------

target_table = f"{catalog_name}.{gold_schema}.dim_races"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read source tables
# MAGIC - `circuits`
# MAGIC - `races`

# COMMAND ----------

circuits_df = spark.table(f"{catalog_name}.{silver_schema}.circuits")
races_df = spark.table(f"{catalog_name}.{silver_schema}.races")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Join `races` with `circuits` using `circuit_id`
# MAGIC Select the following columns  
# MAGIC   1. races.season 
# MAGIC   1. races.round 
# MAGIC   1. races.race_name 
# MAGIC   1. races.race_date 
# MAGIC   1. circuits.circuit_name 
# MAGIC   1. circuits.locality
# MAGIC   1. circuits.country
# MAGIC
# MAGIC An `inner` join is used deliberately: every race in `silver.races` is
# MAGIC expected to reference a valid `circuit_id`, so a race that fails to match
# MAGIC a circuit signals a data-quality problem upstream rather than a case that
# MAGIC should be silently kept with null circuit columns.

# COMMAND ----------

dim_races_df = (
            races_df
                .join(
                    circuits_df,
                    races_df.circuit_id == circuits_df.circuit_id,
                    "inner"
                )
                .select (
                    races_df.season,
                    races_df.round,
                    races_df.race_name,
                    races_df.race_date,
                    circuits_df.circuit_name,
                    circuits_df.locality,
                    circuits_df.country
                )
        )

# COMMAND ----------

display(dim_races_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write the transformed data to the `gold` `dim_races` table
# MAGIC
# MAGIC `overwrite` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project. `dim_races` is small (one row per
# MAGIC race) and cheap to rebuild from the current silver snapshot each time, so
# MAGIC there is no need for incremental merge/upsert logic here.

# COMMAND ----------

(
    dim_races_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))