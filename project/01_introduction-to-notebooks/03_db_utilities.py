# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Utilities
# MAGIC
# MAGIC `dbutils` provides utility functions for common notebook tasks.
# MAGIC
# MAGIC This notebook covers:
# MAGIC
# MAGIC - File system utilities
# MAGIC - Secrets utilities
# MAGIC - Widget utilities
# MAGIC - Notebook workflow utilities

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. File System Utilities
# MAGIC
# MAGIC File system utilities are available under `dbutils.fs`.
# MAGIC
# MAGIC They are useful for listing, creating, copying, moving, and deleting files.

# COMMAND ----------

# MAGIC %fs ls /

# COMMAND ----------

display(dbutils.fs.ls("/"))

# COMMAND ----------

# MAGIC %fs ls dbfs:/databricks-datasets/

# COMMAND ----------

items = dbutils.fs.ls("/databricks-datasets/")

display(items)

# COMMAND ----------

# Count folders and files using list comprehensions

folder_count = len([item for item in items if item.name.endswith("/")])
file_count = len([item for item in items if not item.name.endswith("/")])

print(f"Total folders: {folder_count}")
print(f"Total files: {file_count}")

# COMMAND ----------

# Create a temporary folder for this notebook

demo_path = "/tmp/databricks_intro/utilities_demo"

dbutils.fs.mkdirs(demo_path)

print(f"Created or confirmed folder: {demo_path}")

# COMMAND ----------

# Write a small text file

file_path = f"{demo_path}/hello.txt"

dbutils.fs.put(file_path, "Hello from dbutils.fs.put()", overwrite=True)

print(f"Wrote file: {file_path}")

# COMMAND ----------

# Read the file back

content = dbutils.fs.head(file_path)

print(content)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Help Commands
# MAGIC
# MAGIC Use help commands to inspect available utilities.

# COMMAND ----------

dbutils.help()

# COMMAND ----------

dbutils.fs.help()

# COMMAND ----------

dbutils.fs.help("cp")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Secrets Utilities
# MAGIC
# MAGIC Secrets are managed with `dbutils.secrets`.
# MAGIC
# MAGIC Typical usage:
# MAGIC
# MAGIC ```python
# MAGIC dbutils.secrets.get(scope="my-scope", key="my-key")
# MAGIC ```
# MAGIC
# MAGIC Do not print secrets in notebooks.
# MAGIC
# MAGIC The example below lists available secret scopes if your workspace permits it.

# COMMAND ----------

try:
    scopes = dbutils.secrets.listScopes()
    display(scopes)
except Exception as error:
    print("Could not list secret scopes.")
    print(f"Reason: {error}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Widget Utilities
# MAGIC
# MAGIC Widgets let users parameterize notebooks.

# COMMAND ----------

dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.dropdown("department", "Engineering", ["Engineering", "Sales", "Marketing"], "Department")

# COMMAND ----------

selected_environment = dbutils.widgets.get("environment")
selected_department = dbutils.widgets.get("department")

print(f"Selected environment: {selected_environment}")
print(f"Selected department: {selected_department}")

# COMMAND ----------

# Example data filtered by widget value

employee_data = [
    (1, "Alice", "Engineering"),
    (2, "Bob", "Sales"),
    (3, "Charlie", "Engineering"),
    (4, "Diana", "Marketing"),
]

employees_df = spark.createDataFrame(employee_data, ["id", "name", "department"])

filtered_df = employees_df.filter(employees_df.department == selected_department)

display(filtered_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Notebook Workflow Utilities
# MAGIC
# MAGIC `dbutils.notebook.run()` can run another notebook and return a string result.
# MAGIC
# MAGIC Example:
# MAGIC
# MAGIC ```python
# MAGIC result = dbutils.notebook.run("./Some_Other_Notebook", timeout_seconds=60)
# MAGIC print(result)
# MAGIC ```
# MAGIC
# MAGIC Use notebook workflows carefully. For production orchestration, Databricks Workflows are usually clearer.

# COMMAND ----------

# Example only. Uncomment and adjust the path when the target notebook exists.
#
# result = dbutils.notebook.run("./2.1_Environment_Variables_and_Functions", timeout_seconds=60)
# print(result)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Cleanup
# MAGIC
# MAGIC Cleanup temporary files and widgets when they are no longer needed.

# COMMAND ----------

dbutils.fs.rm(demo_path, recurse=True)

print(f"Removed temporary folder: {demo_path}")

# COMMAND ----------

# Uncomment when you want to remove widgets:
# dbutils.widgets.remove("environment")
# dbutils.widgets.remove("department")

print("Databricks utilities notebook completed.")