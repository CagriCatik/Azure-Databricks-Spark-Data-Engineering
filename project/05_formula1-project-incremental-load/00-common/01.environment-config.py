# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Configuration
# MAGIC
# MAGIC Single source of truth for the Unity Catalog object names used by every
# MAGIC notebook in this project. Every setup, bronze, silver, gold, and
# MAGIC orchestration notebook pulls these constants in with:
# MAGIC
# MAGIC ```text
# MAGIC %run ../00-common/01.environment-config
# MAGIC ```
# MAGIC
# MAGIC `%run` executes this notebook in the caller's own context, so the
# MAGIC variables defined below land directly in the calling notebook's
# MAGIC namespace - Databricks' equivalent of importing a shared config module.
# MAGIC If the catalog or any schema is ever renamed, this is the one file that
# MAGIC needs to change.
# MAGIC
# MAGIC This is the incremental-load counterpart of
# MAGIC `project/04_formula1-project/00-common/01.environment-config.py`. The
# MAGIC only structural difference is `control_schema`: this project tracks
# MAGIC batch state (see `06-orchestration`) in a dedicated schema, which the
# MAGIC full-refresh project has no need for.
# MAGIC
# MAGIC > This notebook only assigns variables - it has no side effects, and
# MAGIC > does not read or write any data itself.

# COMMAND ----------

# Unity Catalog uses a three-level namespace: catalog.schema.table.
# Every downstream notebook builds its fully qualified table name from these
# constants, e.g. f"{catalog_name}.{bronze_schema}.circuits", rather than a
# hardcoded literal - so a single rename here propagates everywhere.
# NOTE: this is the "_incr" catalog - a separate namespace from the
# full-refresh `formula1` catalog used by ../../04_formula1-project, so the
# two projects' tables never collide even when run side by side.
catalog_name = 'formula1_incr'
bronze_schema = 'bronze'
silver_schema = 'silver'
gold_schema = 'gold'
# Schema holding batch-orchestration metadata (see 06-orchestration) - not a
# medallion data layer. It tracks which batch_id is currently being
# processed and its status, so a scheduled job knows which batch to pick up
# next. Created by 06-orchestration/00.Create Control Tables.py.
control_schema = 'control'

# COMMAND ----------

# Unity Catalog volume path for the raw landing files, in the standard
# /Volumes/<catalog>/<schema>/<volume> form. This volume is an EXTERNAL
# volume (raw files are dropped here by a process outside Databricks) - see
# 01-setup/01.Setup Project Environment.sql for how it is created.
#
# Unlike the full-refresh project, each batch's source files live in their
# own numbered subfolder below this path, e.g.
# f"{landing_folder_path}/{batch_id}/circuits.csv" - see any notebook in
# 02-bronze for how the batch_id widget is appended to build the full path.
landing_folder_path = '/Volumes/formula1_incr/landing/files'
