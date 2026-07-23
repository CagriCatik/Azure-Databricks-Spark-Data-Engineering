# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Drivers Data
# MAGIC
# MAGIC 1. Read bronze `drivers` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`driverId` → `driver_id`, `dateOfBirth` → `date_of_birth`)
# MAGIC 1. Concatenate `name.givenName` and `name.familyName` to create a new column called `driver_name` and transform the value to Title Case
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of column `nationality` to Title Case
# MAGIC 1. Write the transformed data to silver `drivers` table
# MAGIC
# MAGIC This notebook builds the silver `drivers` table: bronze data cleaned, renamed,
# MAGIC and de-duplicated on `driver_id`, with the nested `name` struct flattened into a
# MAGIC single display-ready `driver_name` column. Joined by `nationality` against the
# MAGIC gold `ref_nationality_region` reference table (see
# MAGIC `04-gold/03.Build Drivers Dimension`). As with the rest of this project variant,
# MAGIC the final write is a full overwrite - no incremental/batch tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Bronze Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.drivers"
silver_table = f"{catalog_name}.{silver_schema}.drivers"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `drivers` table

# COMMAND ----------

drivers_df = spark.table(bronze_table)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)
# MAGIC
# MAGIC `url` is a link back to the source website with no analytical value. Since it
# MAGIC is the only column being removed, `.drop(...)` is a simpler equivalent to
# MAGIC whitelisting every other column with `.select(...)`.

# COMMAND ----------

drivers_dropped_df = drivers_df.drop(F.col("url"))

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`driverId` → `driver_id`, `dateOfBirth` → `date_of_birth`)
# MAGIC
# MAGIC Bronze mirrors the source API's camelCase fields as-is; silver renames them to
# MAGIC snake_case, the convention expected by Spark SQL, Delta table columns, and
# MAGIC downstream BI tools.

# COMMAND ----------

drivers_renamed_df = (
    drivers_dropped_df
        .withColumnsRenamed({
            "driverId": "driver_id",
            "dateOfBirth": "date_of_birth"
        })
)

# COMMAND ----------

display(drivers_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 4 - Concatenate name.givenName and name.familyName to create a new column called driver_name
# MAGIC
# MAGIC `name` arrives as a nested struct (`name.givenName` / `name.familyName`) rather
# MAGIC than a flat string. Flattening it into a single `driver_name` column - already
# MAGIC title-cased via `F.initcap()` - makes it usable directly in `.select()`,
# MAGIC `GROUP BY`, and reporting tools that don't handle nested struct columns well.
# MAGIC The original nested `name` column is dropped once `driver_name` has been
# MAGIC derived from it.

# COMMAND ----------

drivers_concatenated_df = (
  drivers_renamed_df
       .withColumn("driver_name",
                   F.initcap(F.concat_ws(" ", F.col("name.givenName"), F.col("name.familyName"))))
       .drop("name")
)

# COMMAND ----------

display(drivers_concatenated_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 - Remove duplicate records
# MAGIC
# MAGIC `driver_id` is the business key gold-layer joins rely on (see
# MAGIC `04-gold/03.Build Drivers Dimension`). `dropDuplicates` is scoped to it so any
# MAGIC re-ingested duplicate rows collapse to a single record per driver.

# COMMAND ----------

drivers_distinct_df = drivers_concatenated_df.dropDuplicates(["driver_id"])

# COMMAND ----------

display(drivers_distinct_df)

# COMMAND ----------

# Sanity check: how many duplicate rows were collapsed by dropDuplicates.
display(drivers_concatenated_df.count() - drivers_distinct_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Transform values of column `nationality` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes this free-text display column to Title Case for consistent
# MAGIC presentation, and so it matches cleanly when joined against the `nationality`
# MAGIC column in the gold `ref_nationality_region` reference table.

# COMMAND ----------

drivers_final_df = (
    drivers_distinct_df
        .withColumn('nationality', F.initcap(F.col("nationality")))
)

# COMMAND ----------

display(drivers_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Write the transformed data to silver `drivers` table
# MAGIC
# MAGIC `mode('overwrite')` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project variant (see
# MAGIC `05_formula1-project-incremental-load` for the MERGE/batch-tracking variant).

# COMMAND ----------

(
    drivers_final_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))
