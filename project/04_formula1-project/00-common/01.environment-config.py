# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Configuration
# MAGIC
# MAGIC Single source of truth for the Unity Catalog object names used by every
# MAGIC notebook in this project. Every setup, bronze, silver, and gold notebook
# MAGIC pulls the catalog name and schema names from here with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/01.environment-config
# MAGIC ```
# MAGIC
# MAGIC `%run` executes this notebook in the caller's own context, so the variables
# MAGIC defined below land directly in the calling notebook's namespace - Databricks'
# MAGIC equivalent of importing a shared config module. That is deliberate: about a
# MAGIC dozen notebooks across `01-setup`, `02-bronze`, `03-silver`, and `04-gold`
# MAGIC reference the `formula1` catalog and its `bronze`/`silver`/`gold` schemas, and
# MAGIC none of them hardcode those names directly. If a catalog or schema is ever
# MAGIC renamed, this is the one file that needs to change.
# MAGIC
# MAGIC > This notebook only assigns variables - it has no side effects, and does not
# MAGIC > read or write any data itself.

# COMMAND ----------

# Unity Catalog uses a three-level namespace: catalog.schema.table.
# Every downstream notebook builds its fully qualified table name from these
# constants, e.g. f"{catalog_name}.{bronze_schema}.circuits", rather than a
# hardcoded literal - so a single rename here propagates everywhere.
catalog_name = 'formula1'
bronze_schema = 'bronze'
silver_schema = 'silver'
gold_schema = 'gold'

# COMMAND ----------

# Unity Catalog volume path for the raw landing files, in the standard
# /Volumes/<catalog>/<schema>/<volume> form. This volume is an EXTERNAL volume
# (raw files are dropped here by a process outside Databricks) - see
# 01-setup/01.Setup Project Environment.sql for how it is created.
landing_folder_path = '/Volumes/formula1/landing/files'
