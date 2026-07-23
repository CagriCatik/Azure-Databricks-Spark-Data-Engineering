# Databricks notebook source
# MAGIC %md
# MAGIC # Build Nationality Region Reference
# MAGIC
# MAGIC This notebook is numbered `91`, out of sequence with the `01`-`04` core
# MAGIC pipeline steps in this folder, on purpose: it is a **supplementary
# MAGIC reference notebook**, not a step in the regular bronze -> silver -> gold
# MAGIC dependency chain. It has no silver source table to read - it simply
# MAGIC materializes a static, hand-curated lookup - and both `dim_constructors`
# MAGIC and `dim_drivers` depend on it having already run at least once. The
# MAGIC high numbering keeps it visually separated from, and sorted after, the
# MAGIC core `01`-`04` notebooks, while still signaling "run me before the
# MAGIC dimensions that need me".
# MAGIC
# MAGIC #### Why a static reference table
# MAGIC
# MAGIC Mapping a nationality (e.g. `British`, `Brazilian`) to a broad geographic
# MAGIC region (`Europe`, `South America`, ...) is a classic case for a small,
# MAGIC static **reference/lookup table**: the source data has no region column
# MAGIC to begin with, and the alternative - calling an external geocoding/geo
# MAGIC API at read time - would add a network dependency, latency, and cost to
# MAGIC every pipeline run for a mapping that essentially never changes. A `Row`
# MAGIC literal list curated once and stored as a gold table is simpler, free,
# MAGIC and fully reproducible.
# MAGIC
# MAGIC #### Maintenance limitation
# MAGIC
# MAGIC The trade-off is that this list is **not** self-maintaining. It only
# MAGIC covers the nationalities present in the dataset at the time it was
# MAGIC written. If a new driver or constructor with a nationality not already in
# MAGIC this list appears in a future data refresh, `dim_drivers`/
# MAGIC `dim_constructors` will still include that row (both join to this table
# MAGIC with a `left` join), but its `nationality_region` will silently come back
# MAGIC `NULL` until someone manually adds the new nationality below and reruns
# MAGIC this notebook. There is no automated alert for this - it is a real,
# MAGIC accepted limitation of hand-curated reference data, not a bug.
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
# MAGIC
# MAGIC To add a nationality that is missing (see the maintenance limitation
# MAGIC above): append a `Row(nationality=..., region=...)` to the matching
# MAGIC region group below, then rerun this notebook so
# MAGIC `dim_drivers`/`dim_constructors` pick up the new mapping on their next run.

# COMMAND ----------

from pyspark.sql import Row

# Manually curated nationality → region mapping.
# Grouped and commented by region purely for human readability - the region
# grouping itself carries no meaning to Spark, only the (nationality, region)
# pairs on each Row do.
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
# MAGIC `overwrite` here simply replaces the whole (small) reference table with
# MAGIC the current in-notebook literal - the same full-refresh approach used
# MAGIC throughout this project, just applied to a hand-authored list instead of
# MAGIC a silver source table.

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