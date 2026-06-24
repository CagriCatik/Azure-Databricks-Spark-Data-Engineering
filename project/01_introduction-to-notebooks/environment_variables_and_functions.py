# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Variables and Functions
# MAGIC
# MAGIC This notebook is designed to be imported with `%run`.
# MAGIC
# MAGIC It defines:
# MAGIC
# MAGIC - A simple environment variable named `env`
# MAGIC - A helper function to print runtime information
# MAGIC - A helper function to build environment-specific paths
# MAGIC - A small configuration dictionary

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
# MAGIC Keep shared setup notebooks small and explicit. Avoid hiding too much logic behind `%run`.