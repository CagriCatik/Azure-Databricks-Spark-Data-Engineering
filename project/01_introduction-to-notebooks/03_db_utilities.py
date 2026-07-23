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
# MAGIC File system utilities are available under `dbutils.fs` - the Python API version
# MAGIC of the `%fs` magic command covered in `02_magic_commands.py`. Because it is real
# MAGIC Python rather than a fixed magic syntax, `dbutils.fs` can be used inside loops,
# MAGIC conditionals, and error handling, and it works uniformly against the classic DBFS
# MAGIC root shown below, mount points, and Unity Catalog **Volumes**
# MAGIC (`/Volumes/catalog/schema/volume/...`) - see
# MAGIC `02_introduction-to-unity-catalog/01_uc_introduction.py` for volumes in context.
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
# MAGIC ### Copying and moving files
# MAGIC
# MAGIC `dbutils.fs.cp` and `dbutils.fs.mv` mirror the Unix `cp` and `mv` commands: `cp`
# MAGIC leaves the original file in place, `mv` does not. Both accept `recurse=True` when
# MAGIC the source is a directory rather than a single file.

# COMMAND ----------

copy_path = f"{demo_path}/hello_copy.txt"
moved_path = f"{demo_path}/hello_moved.txt"

dbutils.fs.cp(file_path, copy_path)
print(f"Copied {file_path} -> {copy_path}")

dbutils.fs.mv(copy_path, moved_path)
print(f"Moved {copy_path} -> {moved_path}")

display(dbutils.fs.ls(demo_path))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Help Commands
# MAGIC
# MAGIC Use help commands to inspect available utilities without leaving the notebook.
# MAGIC
# MAGIC - `dbutils.help()` lists the top-level `dbutils` sub-modules (`fs`, `secrets`,
# MAGIC   `widgets`, `notebook`, ...).
# MAGIC - `dbutils.fs.help()` lists every command inside `dbutils.fs`.
# MAGIC - `dbutils.fs.help("cp")` shows the signature and description of just that one
# MAGIC   command - handy for checking whether an option like `recurse` exists before
# MAGIC   reaching for a search engine.

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
# MAGIC **Why this exists at all:** hardcoding a password, API token, or connection
# MAGIC string directly in a notebook cell means it ends up in that notebook's revision
# MAGIC history, in any job definition that references it, and potentially in driver
# MAGIC logs - readable by anyone with access to any of those, and painful to rotate
# MAGIC because you have to hunt down every place it was pasted. `dbutils.secrets.get(...)`
# MAGIC instead fetches the value at runtime from a managed **secret scope**, and
# MAGIC Databricks automatically redacts any output string that matches a fetched
# MAGIC secret's value, replacing it with `[REDACTED]`. That redaction is a safety net,
# MAGIC not a substitute for careful handling - never `print()` a secret on purpose.
# MAGIC
# MAGIC A secret scope is a named container of key-value secrets, backed by one of two
# MAGIC storage types:
# MAGIC
# MAGIC - **Databricks-backed scope** - secrets are stored and encrypted by Databricks
# MAGIC   itself. Created and managed through the Secrets REST API or the Databricks CLI
# MAGIC   (`databricks secrets create-scope`), with access controlled by ACLs on the
# MAGIC   scope.
# MAGIC - **Azure Key Vault-backed scope** - the scope is just a pointer to an existing
# MAGIC   Azure Key Vault instance; Databricks never stores the secret values at all, it
# MAGIC   calls through to Key Vault at read time. Key Vault's own access policies/RBAC
# MAGIC   are what actually govern the secret, and rotating a value in Key Vault takes
# MAGIC   effect immediately with no changes needed on the Databricks side.
# MAGIC
# MAGIC Typical usage:
# MAGIC
# MAGIC ```python
# MAGIC dbutils.secrets.get(scope="my-scope", key="my-key")
# MAGIC ```
# MAGIC
# MAGIC Do not print secrets in notebooks.
# MAGIC
# MAGIC The examples below list available secret scopes, and the key names inside the
# MAGIC first one, without ever reading or printing an actual secret value.

# COMMAND ----------

try:
    scopes = dbutils.secrets.listScopes()
    display(scopes)
except Exception as error:
    print("Could not list secret scopes.")
    print(f"Reason: {error}")
    scopes = []

# COMMAND ----------

# dbutils.secrets.list(scope) returns key *names* only, never values, so it is
# always safe to print. This only produces output if at least one scope exists
# and you have permission to read its key list.

try:
    if scopes:
        first_scope = scopes[0].name
        keys = dbutils.secrets.list(first_scope)
        print(f"Keys in scope '{first_scope}':")
        for key in keys:
            print(f"  {key.key}")
    else:
        print("No secret scopes available to list keys from.")
except Exception as error:
    print("Could not list secret keys.")
    print(f"Reason: {error}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Widget Utilities
# MAGIC
# MAGIC Widgets let users parameterize notebooks. There are four widget types:
# MAGIC
# MAGIC - `text` - free-form string input
# MAGIC - `dropdown` - pick exactly one value from a fixed list
# MAGIC - `combobox` - pick from a fixed list, or type a value that isn't on it
# MAGIC - `multiselect` - pick any number of values from a fixed list, returned as one
# MAGIC   comma-separated string
# MAGIC
# MAGIC `dbutils.widgets.get(...)` (and its older alias `dbutils.widgets.getArgument(...)`)
# MAGIC always returns a plain string, regardless of which widget type produced it.
# MAGIC Widgets persist across detach/reattach until removed with
# MAGIC `dbutils.widgets.remove(...)` or `dbutils.widgets.removeAll()`.

# COMMAND ----------

dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.dropdown("department", "Engineering", ["Engineering", "Sales", "Marketing"], "Department")
dbutils.widgets.combobox("region", "EU", ["EU", "US", "APAC"], "Region")

# COMMAND ----------

selected_environment = dbutils.widgets.get("environment")
selected_department = dbutils.widgets.get("department")
selected_region = dbutils.widgets.get("region")

print(f"Selected environment: {selected_environment}")
print(f"Selected department: {selected_department}")
print(f"Selected region: {selected_region}")

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
# MAGIC `dbutils.notebook.run()` runs another notebook as an **isolated** execution - its
# MAGIC own REPL and Spark session context, not a shared one - and returns a single
# MAGIC string result once it finishes. That isolation is the key difference from `%run`
# MAGIC (covered in `02_magic_commands.py`): `%run` inlines the target notebook's cells
# MAGIC into the caller, sharing every variable and function both ways, while
# MAGIC `dbutils.notebook.run()` only ever gives you back whatever string the child
# MAGIC notebook passed to `dbutils.notebook.exit(...)` - nothing else crosses the
# MAGIC boundary. That isolation makes it a good fit for orchestrating independent
# MAGIC notebooks as steps in a larger workflow, since two notebooks run this way can
# MAGIC never accidentally clobber each other's variables.
# MAGIC
# MAGIC Example:
# MAGIC
# MAGIC ```python
# MAGIC result = dbutils.notebook.run("./Some_Other_Notebook", timeout_seconds=60)
# MAGIC print(result)
# MAGIC ```
# MAGIC
# MAGIC A dictionary passed as the third argument becomes a set of widgets inside the
# MAGIC child notebook - that is how `dbutils.notebook.run()` parameterizes a run.
# MAGIC
# MAGIC Use notebook workflows carefully. For production orchestration, Databricks
# MAGIC Workflows are usually clearer.

# COMMAND ----------

# Example only. Uncomment and adjust the path/timeout when you want to actually
# trigger a run.
#
# Note: this previously pointed at "./2.1_Environment_Variables_and_Functions",
# which does not exist in this folder - corrected below to the real file,
# environment_variables_and_functions.py (the same file %run uses in
# 02_magic_commands.py).
#
# result = dbutils.notebook.run("./environment_variables_and_functions", timeout_seconds=60)
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
# dbutils.widgets.remove("region")

print("Databricks utilities notebook completed.")
