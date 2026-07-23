# Databricks notebook source
# MAGIC %md
# MAGIC # Transform Constructors Data
# MAGIC
# MAGIC 1. Read bronze `constructors` table
# MAGIC 1. Keep only the columns required for analytics (Drop `url` column)
# MAGIC 1. Standardise column names using snake_case (`constructorId` → `constructor_id`)
# MAGIC 1. Rename columns to make them more meaningful (`name` → `constructor_name`)
# MAGIC 1. Remove duplicate records
# MAGIC 1. Transform values of column `nationality` to Title Case
# MAGIC 1. Write the transformed data to silver `constructors` table
# MAGIC
# MAGIC This notebook builds the silver `constructors` table: bronze data cleaned,
# MAGIC renamed, and de-duplicated on `constructor_id` so it can be joined by
# MAGIC `nationality` against the gold `ref_nationality_region` reference table (see
# MAGIC `04-gold/02.Build Constructors Dimension`). As with the rest of this project
# MAGIC variant, the final write is a full overwrite - no incremental/batch tracking.

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC #### Entity Relationship Diagram - Formula1 Bronze Schema
# MAGIC
# MAGIC ![Formula1 Raw Data.png](../../z-course-images/formula1-raw-data-erd.png "Formula1 Raw Data.png")

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

bronze_table = f"{catalog_name}.{bronze_schema}.constructors"
silver_table = f"{catalog_name}.{silver_schema}.constructors"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Read bronze `constructors` table

# COMMAND ----------

constructors_df = spark.table(bronze_table)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Keep only the columns required for analytics (Drop url column)
# MAGIC
# MAGIC `url` is a link back to the source website with no analytical value. Since it
# MAGIC is the only column being removed, `.drop("url")` is a simpler equivalent to
# MAGIC whitelisting every other column with `.select(...)` (the approach used
# MAGIC elsewhere in this folder, e.g. `circuits`/`races`).

# COMMAND ----------

constructors_dropped_df = constructors_df.drop("url")

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 3 & 4 - Standardise Column Names
# MAGIC - Standardise column names using snake_case (`constructorId` → `constructor_id`)
# MAGIC - Rename columns to make them more meaningful (`name` → `constructor_name`)
# MAGIC
# MAGIC Bronze mirrors the source API's camelCase fields as-is; silver renames them to
# MAGIC snake_case, the convention expected by Spark SQL, Delta table columns, and
# MAGIC downstream BI tools. `name` is also renamed to `constructor_name` since a bare
# MAGIC `name` column would be ambiguous once this table sits alongside `drivers`
# MAGIC (which has its own `driver_name`) in gold-layer queries.

# COMMAND ----------

constructors_renamed_df = (
    constructors_dropped_df
        .withColumnsRenamed({
            "constructorId": "constructor_id",
            "name": "constructor_name"
        })
)

# COMMAND ----------

display(constructors_renamed_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 5 - Remove duplicate records
# MAGIC
# MAGIC `constructor_id` is the business key gold-layer joins rely on (see
# MAGIC `04-gold/02.Build Constructors Dimension`). `dropDuplicates` is scoped to it so
# MAGIC any re-ingested duplicate rows collapse to a single record per constructor.

# COMMAND ----------

constructors_distinct_df = constructors_renamed_df.dropDuplicates(["constructor_id"])

# COMMAND ----------

display(constructors_distinct_df)

# COMMAND ----------

# Sanity check: how many duplicate rows were collapsed by dropDuplicates.
display(constructors_renamed_df.count() - constructors_distinct_df.count())

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 6 - Transform values of column `nationality` to Title Case
# MAGIC
# MAGIC Source values arrive inconsistently cased depending on the feed. `F.initcap()`
# MAGIC normalizes this free-text display column to Title Case for consistent
# MAGIC presentation, and so it matches cleanly when joined against the `nationality`
# MAGIC column in the gold `ref_nationality_region` reference table.

# COMMAND ----------

constructors_final_df = (
    constructors_distinct_df
        .withColumn('nationality', F.initcap(F.col("nationality")))
)

# COMMAND ----------

display(constructors_final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 7 - Write the transformed data to silver `constructors` table
# MAGIC
# MAGIC `mode('overwrite')` fully replaces the table on every run - the full-refresh
# MAGIC strategy used throughout this project variant (see
# MAGIC `05_formula1-project-incremental-load` for the MERGE/batch-tracking variant).

# COMMAND ----------

(
    constructors_final_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(silver_table)
)

# COMMAND ----------

display(spark.table(silver_table))
