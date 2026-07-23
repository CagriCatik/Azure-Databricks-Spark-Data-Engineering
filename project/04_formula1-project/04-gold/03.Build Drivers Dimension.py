# Databricks notebook source
# MAGIC %md
# MAGIC # Build Drivers Dimension
# MAGIC
# MAGIC Builds the `dim_drivers` dimension: one row per driver, enriched with a
# MAGIC geographic region derived from nationality. Like `dim_constructors`, this
# MAGIC is a descriptive, slowly-changing business entity - drivers rarely change
# MAGIC name or nationality - joined against the same shared reference table,
# MAGIC `gold.ref_nationality_region` (see `91.Build Nationality Region
# MAGIC Reference`).
# MAGIC
# MAGIC 1. Read silver `drivers` table
# MAGIC 1. Read gold `ref_nationality_region` table
# MAGIC 1. Join the data from `drivers` with `ref_nationality_region` using `nationality`
# MAGIC 1. Select the required columns
# MAGIC     - drivers.driver_id
# MAGIC     - drivers.driver_name
# MAGIC     - drivers.date_of_birth
# MAGIC     - drivers.nationality
# MAGIC     - ref_nationality_region.region
# MAGIC 1. Write the transformed data to gold `dim_drivers` table
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

target_table = f"{catalog_name}.{gold_schema}.dim_drivers"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read source tables
# MAGIC - `silver.drivers`
# MAGIC - `gold.ref_nationality_region`

# COMMAND ----------

drivers_df               = spark.table(f"{catalog_name}.{silver_schema}.drivers")
ref_nationality_region_df = spark.table(f"{catalog_name}.{gold_schema}.ref_nationality_region")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Join `drivers` with `nationality_region_df` using `nationality`
# MAGIC Select the following columns   
# MAGIC 1. drivers.driver_id
# MAGIC 1. drivers.driver_name
# MAGIC 1. drivers.date_of_birth
# MAGIC 1. drivers.nationality
# MAGIC 1. ref_nationality_region.region
# MAGIC
# MAGIC As in `dim_constructors`, a `left` join is used because
# MAGIC `ref_nationality_region` is a manually maintained lookup and may not cover
# MAGIC every nationality yet - a `left` join keeps every driver and leaves
# MAGIC `nationality_region` null for any unmapped nationality, instead of
# MAGIC dropping the driver from the dimension entirely.

# COMMAND ----------

dim_drivers_df = (
    drivers_df
        .join(
            ref_nationality_region_df,
            drivers_df.nationality == ref_nationality_region_df.nationality,
            "left"
        )
        .select(
            drivers_df.driver_id,
            drivers_df.driver_name,
            drivers_df.date_of_birth,
            drivers_df.nationality,
            ref_nationality_region_df.region.alias("nationality_region")  # aliased so it reads unambiguously as a nationality-derived attribute
        )
)

# COMMAND ----------

display(dim_drivers_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write the transformed data to the `gold` `dim_drivers` table
# MAGIC
# MAGIC `overwrite` fully replaces the table on every run - the same full-refresh
# MAGIC strategy used across all gold notebooks in this project (see
# MAGIC `01.Build Races Dimension` for the reasoning).

# COMMAND ----------

(
    dim_drivers_df
        .write
        .format("delta")
        .mode("overwrite")             
        .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))