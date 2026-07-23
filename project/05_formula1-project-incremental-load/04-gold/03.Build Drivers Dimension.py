# Databricks notebook source
# MAGIC %md
# MAGIC # Build Drivers Dimension
# MAGIC
# MAGIC Builds the gold `dim_drivers` dimension at a grain of one row per
# MAGIC `driver_id`, enriching each driver with a geographic `region` derived from
# MAGIC `nationality`. `date_of_birth` and `nationality` are effectively immutable
# MAGIC per driver, but the merge still refreshes them like any Type 1 attribute in
# MAGIC case a data-quality correction arrives in a later batch.
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

dbutils.widgets.text("p_batch_id", "")
v_batch_id = dbutils.widgets.get("p_batch_id")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

# MAGIC %run ../00-common/04.gold-helpers

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

drivers_df = (
    spark.table(f"{catalog_name}.{silver_schema}.drivers")
         .filter(F.col("batch_id") == v_batch_id)
)

# COMMAND ----------

ref_nationality_region_df = spark.table(f"{catalog_name}.{gold_schema}.ref_nationality_region")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Join `drivers` with `nationality_region_df` using `nationality`
# MAGIC A `left` join is used deliberately: if a driver's `nationality` is not (yet)
# MAGIC present in `ref_nationality_region` (see notebook `91`), the driver is still
# MAGIC written to gold with `nationality_region` set to `null` rather than being
# MAGIC silently dropped from the dimension.
# MAGIC
# MAGIC Select the following columns
# MAGIC 1. drivers.driver_id
# MAGIC 1. drivers.driver_name
# MAGIC 1. drivers.date_of_birth
# MAGIC 1. drivers.nationality
# MAGIC 1. ref_nationality_region.region

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
            ref_nationality_region_df.region.alias("nationality_region")
        )
)

# COMMAND ----------

display(dim_drivers_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write the transformed data to the `gold` `dim_drivers` table
# MAGIC
# MAGIC Merges on the business key `driver_id`. `created_timestamp` is stamped only
# MAGIC on first insert by `write_to_gold`; every other listed column is refreshed
# MAGIC whenever a matching row is merged again.

# COMMAND ----------

write_to_gold(
    input_df=dim_drivers_df,
    target_table=target_table,
    merge_condition="t.driver_id = s.driver_id",
    columns_to_update=[
        "driver_name",
        "date_of_birth",
        "nationality",
        "nationality_region"
    ]
)

# COMMAND ----------

display(spark.table(target_table))