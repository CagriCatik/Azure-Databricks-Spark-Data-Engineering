# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Magic Commands
# MAGIC
# MAGIC Magic commands allow you to change the behavior or language of a notebook cell.
# MAGIC
# MAGIC This notebook covers:
# MAGIC
# MAGIC - `%python`, `%scala`, `%sql`, `%r`
# MAGIC - `%md`
# MAGIC - `%fs`
# MAGIC - `%sh`
# MAGIC - `%pip`
# MAGIC - `%run`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Language Magic Commands
# MAGIC
# MAGIC A Databricks notebook has a default language, but individual cells can use another language.
# MAGIC
# MAGIC Common language magic commands:
# MAGIC
# MAGIC - `%python`
# MAGIC - `%sql`
# MAGIC - `%scala`
# MAGIC - `%r`
# MAGIC
# MAGIC The examples below use Python and SQL because they work in most Databricks workspaces.

# COMMAND ----------

message = "Hello from a Python magic cell"
print(message)

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'Hello from a SQL magic cell' AS message;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Markdown Magic: `%md`
# MAGIC
# MAGIC Markdown cells are used to document notebooks.
# MAGIC
# MAGIC You can add:
# MAGIC
# MAGIC - Headings
# MAGIC - Bullet lists
# MAGIC - Numbered lists
# MAGIC - Inline code
# MAGIC - Code blocks
# MAGIC - Links

# COMMAND ----------

# MAGIC %md
# MAGIC ### Markdown Example
# MAGIC
# MAGIC This is a markdown section.
# MAGIC
# MAGIC - Use markdown to explain what the code does.
# MAGIC - Keep explanations close to the related code.
# MAGIC - Make notebooks readable from top to bottom.
# MAGIC
# MAGIC Inline code example: `display(df)`

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. File System Magic: `%fs`
# MAGIC
# MAGIC `%fs` runs Databricks file system commands.
# MAGIC
# MAGIC Use it for quick inspection of folders and files.

# COMMAND ----------

# MAGIC %fs ls /

# COMMAND ----------

# MAGIC %fs ls /databricks-datasets/

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Shell Magic: `%sh`
# MAGIC
# MAGIC `%sh` runs shell commands on the driver node.
# MAGIC
# MAGIC Use this for lightweight environment checks.
# MAGIC
# MAGIC Avoid using `%sh` for production data workflows unless there is a clear reason.

# COMMAND ----------

# MAGIC %sh
# MAGIC echo "Current working directory:"
# MAGIC pwd
# MAGIC
# MAGIC echo "Python executable:"
# MAGIC which python
# MAGIC
# MAGIC echo "First few running processes:"
# MAGIC ps | head

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Package Management Magic: `%pip`
# MAGIC
# MAGIC `%pip` installs Python packages into the notebook environment.
# MAGIC
# MAGIC In real projects, prefer pinned versions, for example:
# MAGIC
# MAGIC ```python
# MAGIC %pip install faker==25.9.1
# MAGIC ```
# MAGIC
# MAGIC After installing packages, Databricks may require the Python process to restart.

# COMMAND ----------

# MAGIC %pip list

# COMMAND ----------

# MAGIC %md
# MAGIC ### Optional install example
# MAGIC
# MAGIC The next cell is commented out to avoid changing the environment automatically.
# MAGIC Uncomment it only when you want to install `faker`.

# COMMAND ----------

# MAGIC %pip install faker

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Notebook Import Magic: `%run`
# MAGIC
# MAGIC `%run` includes another notebook into the current notebook.
# MAGIC
# MAGIC It is commonly used for:
# MAGIC
# MAGIC - Shared configuration
# MAGIC - Shared helper functions
# MAGIC - Reusable setup code
# MAGIC
# MAGIC Example:
# MAGIC
# MAGIC ```python
# MAGIC %run "./environment_variables_and_functions"
# MAGIC ```
# MAGIC
# MAGIC The imported notebook must exist at the referenced path.

# COMMAND ----------

# MAGIC %run "./environment_variables_and_functions"

# COMMAND ----------

# If the imported notebook defines `env`, this cell should print it.
# If the %run cell above was skipped or the path is different, this variable may not exist.

try:
    print(f"Environment from imported notebook: {env}")
except NameError:
    print("The variable `env` is not defined. Check the %run path or run the setup notebook first.")

# COMMAND ----------

# If the imported notebook defines `print_env_info`, this cell should call it.

try:
    print_env_info()
except NameError:
    print("The function `print_env_info()` is not defined. Check the %run path or run the setup notebook first.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Summary
# MAGIC
# MAGIC Magic commands make notebooks more flexible.
# MAGIC
# MAGIC Recommended usage:
# MAGIC
# MAGIC - Use `%md` for documentation.
# MAGIC - Use `%sql` for readable SQL examples.
# MAGIC - Use `%fs` for quick filesystem checks.
# MAGIC - Use `%sh` only when driver-node shell access is necessary.
# MAGIC - Use `%pip` carefully and prefer pinned versions.
# MAGIC - Use `%run` for small shared setup notebooks, not for large hidden dependencies.