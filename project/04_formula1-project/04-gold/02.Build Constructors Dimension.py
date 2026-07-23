# Databricks notebook source
# MAGIC %md
# MAGIC # Build Constructors Dimension
# MAGIC
# MAGIC Builds the `dim_constructors` dimension: one row per constructor (team),
# MAGIC enriched with a geographic region derived from its nationality. The
# MAGIC region lookup comes from `gold.ref_nationality_region` - a small,
# MAGIC hand-curated reference table (see `91.Build Nationality Region
# MAGIC Reference`), not an operational business entity, so this join is really
# MAGIC an "outrigger" onto a reference dimension shared with `dim_drivers`.
# MAGIC
# MAGIC 1. Read silver `constructors` table
# MAGIC 1. Read gold `ref_nationality_region` table
# MAGIC 1. Join the data from `constructors` with `ref_nationality_region` using `nationality`
# MAGIC 1. Select the required columns
# MAGIC     - constructors.constructor_id
# MAGIC     - constructors.constructor_name
# MAGIC     - constructors.nationality
# MAGIC     - ref_nationality_region.region
# MAGIC 1. Write the transformed data to gold `dim_constructors` table
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

target_table = f"{catalog_name}.{gold_schema}.dim_constructors"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read source tables
# MAGIC - `silver.constructors`
# MAGIC - `gold.ref_nationality_region`

# COMMAND ----------

constructors_df = spark.table(f"{catalog_name}.{silver_schema}.constructors")
ref_nationality_region_df = spark.table(f"{catalog_name}.{gold_schema}.ref_nationality_region")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Join `constructors` with `nationality_region_df` using `nationality`
# MAGIC Select the following columns   
# MAGIC 1. constructors.constructor_id 
# MAGIC 1. constructors.constructor_name 
# MAGIC 1. constructors.nationality
# MAGIC 1. ref_nationality_region.region
# MAGIC
# MAGIC A `left` join is used here, not `inner`: `ref_nationality_region` is a
# MAGIC manually maintained lookup, so it may not yet have an entry for every
# MAGIC nationality present in the source data. A `left` join keeps every
# MAGIC constructor and simply leaves `nationality_region` null when no mapping
# MAGIC exists yet, instead of silently dropping the constructor from the
# MAGIC dimension.

# COMMAND ----------

dim_constructors_df = (
    constructors_df
        .join(
            ref_nationality_region_df,
            constructors_df.nationality == ref_nationality_region_df.nationality,
            "left"
            )
        .select (
            constructors_df.constructor_id,
            constructors_df.constructor_name,
            constructors_df.nationality,
            ref_nationality_region_df.region.alias("nationality_region")  # aliased so it reads unambiguously as a nationality-derived attribute, not a circuit/geographic region
        )
)

# COMMAND ----------

display(dim_constructors_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Write the transformed data to the `gold` `dim_constructors` table
# MAGIC
# MAGIC `overwrite` fully replaces the table on every run - the same full-refresh
# MAGIC strategy used across all gold notebooks in this project (see
# MAGIC `01.Build Races Dimension` for the reasoning).

# COMMAND ----------

(
    dim_constructors_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))