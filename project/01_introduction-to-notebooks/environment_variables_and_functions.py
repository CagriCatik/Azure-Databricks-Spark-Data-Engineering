# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Variables and Functions
# MAGIC
# MAGIC This notebook is designed to be imported with `%run`, not run as a standalone
# MAGIC step on its own. `%run` executes a notebook's cells inline, inside the caller's
# MAGIC own Python process and Spark session - which is exactly why every name defined
# MAGIC here (`env`, `print_env_info`, `get_base_path`, `config`, `print_config`) becomes
# MAGIC directly usable in whichever notebook imports it, with no extra syntax. See
# MAGIC `02_magic_commands.py` in this folder for the full `%run` vs
# MAGIC `dbutils.notebook.run()` comparison.
# MAGIC
# MAGIC It defines:
# MAGIC
# MAGIC - A simple environment variable named `env`
# MAGIC - A helper function to print runtime information
# MAGIC - A helper function to build environment-specific paths
# MAGIC - A small configuration dictionary
# MAGIC
# MAGIC This notebook intentionally contains no credentials or connection strings. If a
# MAGIC shared setup notebook like this one ever needed one, it should be fetched with
# MAGIC `dbutils.secrets.get(...)` (see `03_db_utilities.py`) at the point of use, never
# MAGIC hardcoded here.

# COMMAND ----------

env = "dev"

# COMMAND ----------

import os
import platform
from datetime import datetime

# COMMAND ----------

def print_env_info():
    """Print basic notebook and runtime environment information."""

    print(f"Environment: {env}")
    print(f"Python Version: {platform.python_version()}")

    runtime_version = os.environ.get("DATABRICKS_RUNTIME_VERSION", "Unknown")
    print(f"Databricks Runtime Version: {runtime_version}")

    cluster_id = os.environ.get("DB_CLUSTER_ID", "Unknown")
    print(f"Cluster ID: {cluster_id}")

    print(f"Current UTC Time: {datetime.utcnow().isoformat()}Z")

# COMMAND ----------

print_env_info()

# COMMAND ----------

def get_base_path(environment):
    """Return a base path for a given environment."""

    allowed_environments = {"dev", "test", "prod"}

    if environment not in allowed_environments:
        raise ValueError(f"Unsupported environment: {environment}")

    return f"/tmp/databricks_intro/{environment}"

# COMMAND ----------

base_path = get_base_path(env)

print(f"Base path: {base_path}")

# COMMAND ----------

config = {
    "env": env,
    "base_path": base_path,
    "input_path": f"{base_path}/input",
    "output_path": f"{base_path}/output",
    "checkpoint_path": f"{base_path}/checkpoint",
}

config

# COMMAND ----------

def print_config(configuration):
    """Print configuration values in a readable format."""

    for key, value in configuration.items():
        print(f"{key}: {value}")

# COMMAND ----------

print_config(config)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Usage from another notebook
# MAGIC
# MAGIC You can import this notebook from another notebook with:
# MAGIC
# MAGIC ```python
# MAGIC %run "./environment_variables_and_functions"
# MAGIC ```
# MAGIC
# MAGIC After that, the importing notebook can use:
# MAGIC
# MAGIC ```python
# MAGIC env
# MAGIC config
# MAGIC print_env_info()
# MAGIC get_base_path("dev")
# MAGIC ```
# MAGIC
# MAGIC Keep shared setup notebooks small and explicit. Avoid hiding too much logic
# MAGIC behind `%run`.
# MAGIC
# MAGIC One more thing worth noticing: this notebook never calls
# MAGIC `dbutils.notebook.exit(...)`, on purpose - it is meant to be inlined with `%run`,
# MAGIC not launched with `dbutils.notebook.run()`. If something did call it with
# MAGIC `dbutils.notebook.run()` instead, none of the variables or functions above would
# MAGIC be shared back to the caller, and the returned result string would simply be
# MAGIC empty - see `03_db_utilities.py` for that contrast in practice.
