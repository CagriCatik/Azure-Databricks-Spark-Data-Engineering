# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Circuits Data
# MAGIC
# MAGIC 1. Read bronze `circuits` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`circuitId` → `circuit_id`, `circuitName` → `circuit_name`)
# MAGIC 1. Rename columns to make them more meaningful (`lat` → `latitude`, `long` → `longitude`)
# MAGIC 1. Filter out rows where `circuit_id` is null (business key validation)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of columns `circuit_name` and `locality` to Title Case
# MAGIC 1. Write the transformed data to silver `circuits` table
# MAGIC
# MAGIC This notebook builds the silver `circuits` table: bronze data cleaned, conformed
# MAGIC to snake_case naming, and de-duplicated on its business key so it can be joined
# MAGIC safely by `circuit_id` downstream (see `04-gold/01.Build Races Dimension`). As
# MAGIC with the rest of this project variant, the final write is a full overwrite -
# MAGIC there is no incremental/batch tracking here.

# COMMAND ----------

# MAGIC %md
# MAGIC #### Entity Relationship Diagram - Formula1 Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.circuits"
silver_table = f"{catalog_name}.{silver_schema}.circuits"

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `circuits` table

# COMMAND ----------

# Time-travel example (commented out): Delta Lake keeps prior table versions, so
# 'versionAsOf' can pin a read to a specific historical snapshot instead of the
# latest one - useful for reproducing a past run or debugging a regression.
# circuits_df = spark.read.option('versionAsOf', 0).table(bronze_table)

# COMMAND ----------

circuits_df = spark.table(bronze_table)

# COMMAND ----------

display(circuits_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)
# MAGIC
# MAGIC `url` is a link back to the source website with no analytical value - dropping
# MAGIC it here keeps the silver table lean instead of carrying dead weight through
# MAGIC every downstream read.

# COMMAND ----------

# Equivalent using plain column-name strings instead of F.col(...) - either form
# works with .select(); F.col(...) is used below so the column reference can be
# composed with other functions (as happens later in this pipeline).
# circuits_selected_df = circuits_df.select(
#     "circuitId",
#     "circuitName",
#     "lat",
#     "long",
#     "locality",
#     "country",
#     "ingestion_timestamp",
#     "source_file"
# )

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

circuits_selected_df = circuits_df.select(
    F.col("circuitId"),
    F.col("circuitName"),
    F.col("lat"),
    F.col("long"),
    F.col("locality"),
    F.col("country"),
    F.col("ingestion_timestamp"),
    F.col("source_file")
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`circuitId` → `circuit_id`, `circuitName` → `circuit_name`)
# MAGIC - Rename columns to make them more meaningful (`lat` → `latitude`, `long` → `longitude`)
# MAGIC
# MAGIC Bronze mirrors the source API's camelCase fields as-is, since bronze's job is to
# MAGIC preserve raw data untouched. Silver renames them to snake_case - the convention
# MAGIC Spark SQL, Delta table columns, and downstream BI tools expect - and gives the
# MAGIC terse `lat`/`long` abbreviations clearer, self-documenting names.

# COMMAND ----------

# Equivalent using one .withColumnRenamed() call per column instead of the single
# .withColumnsRenamed(dict) call below - functionally identical, just more verbose.
# circuits_renamed_df = (
#     circuits_selected_df
#         .withColumnRenamed("circuitId", "circuit_id")
#         .withColumnRenamed("circuitName", "circuit_name")
#         .withColumnRenamed("lat", "latitude")
#         .withColumnRenamed("long", "longitude")
# )

# COMMAND ----------

circuits_renamed_df = (
    circuits_selected_df
        .withColumnsRenamed({
            "circuitId": "circuit_id",
            "circuitName": "circuit_name",
            "lat": "latitude",
            "long": "longitude"
        })
)

# COMMAND ----------

display(circuits_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 - Filter out rows where circuit_id is null (business key validation)
# MAGIC
# MAGIC `circuit_id` is the business key gold-layer joins rely on (see
# MAGIC `04-gold/01.Build Races Dimension`). A row with a null key can never be joined,
# MAGIC so it is dropped here rather than silently surfacing as an unmatched row later.

# COMMAND ----------

# Equivalent using a SQL filter expression string instead of the F.col(...) form.
# circuits_valid_df = circuits_renamed_df.filter(
#     "circuit_id IS NOT NULL"
# )

# COMMAND ----------

circuits_valid_df = circuits_renamed_df.filter(
    F.col("circuit_id").isNotNull()
)

# COMMAND ----------

display(circuits_valid_df)

# COMMAND ----------

# Sanity check: how many rows were dropped for having a null circuit_id.
display(circuits_renamed_df.count() - circuits_valid_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Remove duplicate records
# MAGIC
# MAGIC Re-running bronze ingestion against the same source file can re-introduce
# MAGIC exact-duplicate rows. `dropDuplicates` is scoped to the business key
# MAGIC (`circuit_id`) rather than a plain `.distinct()`, which would only catch rows
# MAGIC that match on every single column.

# COMMAND ----------

# .distinct() would only remove rows identical across *every* column - too strict
# here, since two ingestion runs of the same circuit could differ in
# ingestion_timestamp/source_file while still being the same logical circuit.
# circuits_distinct_df = circuits_valid_df.distinct()

# COMMAND ----------

circuits_distinct_df = circuits_valid_df.dropDuplicates(["circuit_id"])

# COMMAND ----------

display(circuits_distinct_df)

# COMMAND ----------

# Sanity check: how many duplicate rows were collapsed by dropDuplicates.
display(circuits_valid_df.count() - circuits_distinct_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Transform values of columns `circuit_name` and `locality` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes these free-text display columns to Title Case for consistent
# MAGIC presentation in reports and dashboards.

# COMMAND ----------

circuits_final_df = (
    circuits_distinct_df
        .withColumn('circuit_name', F.initcap(F.col("circuit_name")))
        .withColumn('locality', F.initcap(F.col("locality")))
)

# COMMAND ----------

display(circuits_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 8 - Write the transformed data to silver `circuits` table
# MAGIC
# MAGIC `mode('overwrite')` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project variant (see
# MAGIC `05_formula1-project-incremental-load` for the MERGE/batch-tracking variant).

# COMMAND ----------

(
    circuits_final_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))

# COMMAND ----------

