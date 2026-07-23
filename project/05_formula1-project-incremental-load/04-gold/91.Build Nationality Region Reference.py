# Databricks notebook source
# MAGIC %md
# MAGIC # Build Nationality Region Reference
# MAGIC
# MAGIC Builds the gold `ref_nationality_region` table: a small, hand-curated
# MAGIC lookup from a driver/constructor `nationality` string to a coarser
# MAGIC geographic `region`, used by `dim_constructors` and `dim_drivers` to
# MAGIC support region-level rollups.
# MAGIC
# MAGIC Unlike every other notebook in `04-gold`, this one takes **no**
# MAGIC `p_batch_id` parameter and reads nothing from silver — it isn't sourced
# MAGIC from the batch-partitioned landing files at all, so there is no batch to
# MAGIC filter by. The entire lookup is (re)created from a literal list in code and
# MAGIC the table is fully `overwrite`n on every run, which is the right approach
# MAGIC for a static reference table: there is nothing to incrementally merge, and
# MAGIC overwriting guarantees the table always matches exactly what's defined
# MAGIC below.
# MAGIC
# MAGIC The `91.` prefix (rather than continuing the `01`-`04` sequence) marks this
# MAGIC as a supplementary/reference notebook, not a core pipeline step: it must run
# MAGIC at least once before `02.Build Constructors Dimension` and
# MAGIC `03.Build Drivers Dimension` (both left-join against it), but it is not part
# MAGIC of the per-batch orchestration in `06-orchestration` and does not need to
# MAGIC run on every batch.
# MAGIC
# MAGIC **Maintenance note:** the mapping below is a manually curated list. If a new
# MAGIC `nationality` value ever appears in the source data (e.g. a driver from a
# MAGIC country not yet represented), it will not automatically get a region — the
# MAGIC left joins in `dim_constructors` / `dim_drivers` will simply leave
# MAGIC `nationality_region` as `null` for that row until someone adds the new
# MAGIC nationality here and reruns this notebook.
# MAGIC
# MAGIC 1. Create a dataframe with list of nationalities and corresponding geographic regions
# MAGIC 1. Write the dataframe to gold `ref_nationality_region` table
# MAGIC

# COMMAND ----------

# MAGIC %run ../00-common/01.environment-config

# COMMAND ----------

target_table = f"{catalog_name}.{gold_schema}.ref_nationality_region"

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 1 - Create a dataframe with list of nationalities and corresponding geographic regions

# COMMAND ----------

from pyspark.sql import Row

# Manually curated nationality → region mapping
nationality_region_map_rows = [
    # Europe
    Row(nationality="British",           region="Europe"),
    Row(nationality="Italian",           region="Europe"),
    Row(nationality="French",            region="Europe"),
    Row(nationality="German",            region="Europe"),
    Row(nationality="Swiss",             region="Europe"),
    Row(nationality="Dutch",             region="Europe"),
    Row(nationality="Belgium",           region="Europe"),
    Row(nationality="Belgian",           region="Europe"),
    Row(nationality="Irish",             region="Europe"),
    Row(nationality="Spanish",           region="Europe"),
    Row(nationality="Austrian",          region="Europe"),
    Row(nationality="East German",       region="Europe"),
    Row(nationality="Russian",           region="Europe"),
    Row(nationality="Finnish",           region="Europe"),
    Row(nationality="Polish",            region="Europe"),
    Row(nationality="Portuguese",        region="Europe"),
    Row(nationality="Hungarian",         region="Europe"),
    Row(nationality="Danish",            region="Europe"),
    Row(nationality="Czech",             region="Europe"),
    Row(nationality="Liechtensteiner",   region="Europe"),
    Row(nationality="Monegasque",        region="Europe"),
    Row(nationality="Swedish",           region="Europe"),
    Row(nationality="Argentine-italian", region="Europe"),
    Row(nationality="American-italian",  region="Europe"),

    # North America
    Row(nationality="American",          region="North America"),
    Row(nationality="Canadian",          region="North America"),
    Row(nationality="Mexican",           region="North America"),

    # South America
    Row(nationality="Brazilian",         region="South America"),
    Row(nationality="Chilean",           region="South America"),
    Row(nationality="Argentine",         region="South America"),
    Row(nationality="Uruguayan",         region="South America"),
    Row(nationality="Venezuelan",        region="South America"),
    Row(nationality="Colombian",         region="South America"),

    # Africa
    Row(nationality="South African",     region="Africa"),
    Row(nationality="Rhodesian",         region="Africa"),

    # Asia
    Row(nationality="Indian",            region="Asia"),
    Row(nationality="Chinese",           region="Asia"),
    Row(nationality="Japanese",          region="Asia"),
    Row(nationality="Malaysian",         region="Asia"),
    Row(nationality="Hong Kong",         region="Asia"),
    Row(nationality="Indonesian",        region="Asia"),
    Row(nationality="Thai",              region="Asia"),

    # Oceania
    Row(nationality="Australian",        region="Oceania"),
    Row(nationality="New Zealand",       region="Oceania"),
    Row(nationality="New Zealander",     region="Oceania"),
]

ref_nationality_region_df = spark.createDataFrame(nationality_region_map_rows)



# COMMAND ----------

# MAGIC %md
# MAGIC #### Step 2 - Write the dataframe to the `gold` `ref_nationality_region` table
# MAGIC
# MAGIC A plain `overwrite` is used here instead of `write_to_gold` — there is no
# MAGIC `batch_id`, no incremental slice, and no history to preserve, so replacing
# MAGIC the whole (small) table on every run is simplest and always correct.

# COMMAND ----------

(
    ref_nationality_region_df
        .write
        .format("delta")
        .mode("overwrite")             
        .saveAsTable(target_table)
)

# COMMAND ----------

display(spark.table(target_table))