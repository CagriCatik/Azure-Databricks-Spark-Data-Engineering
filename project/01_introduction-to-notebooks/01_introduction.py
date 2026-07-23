# Databricks notebook source
# MAGIC %md
# MAGIC # Introduction to Databricks Notebooks
# MAGIC
# MAGIC Databricks notebooks combine **documentation**, **code**, **SQL**, **visualizations**,
# MAGIC and **collaboration** in one place. A single notebook can mix cells written in
# MAGIC different languages, render rich Markdown alongside runnable code, and later be
# MAGIC scheduled as a production job without any changes - the same file you explore
# MAGIC interactively is the file that runs unattended.
# MAGIC
# MAGIC In this notebook we will cover:
# MAGIC
# MAGIC - Notebook structure and the execution model
# MAGIC - Markdown cells
# MAGIC - Python cells
# MAGIC - SQL cells
# MAGIC - Magic commands
# MAGIC - Widgets
# MAGIC - Spark DataFrames
# MAGIC - Temporary SQL views
# MAGIC - Basic visualizations
# MAGIC - File system and shell examples
# MAGIC - Notebook best practices

# COMMAND ----------

# MAGIC %md
# MAGIC ## 0. Notebook Structure and Execution Model
# MAGIC
# MAGIC A Databricks notebook is a plain text file under the hood. The very first line,
# MAGIC `# Databricks notebook source`, is what tells Databricks (and this repository's
# MAGIC source-format export) to treat the file as a notebook rather than a regular
# MAGIC script. From there, the file is split into **cells** by `# COMMAND ----------`
# MAGIC markers - each cell is one independently runnable unit, shown as its own block in
# MAGIC the UI.
# MAGIC
# MAGIC Every notebook also has one **default language**, chosen when the notebook is
# MAGIC created (this one is Python). A plain cell with no magic command runs in that
# MAGIC default language; a cell that starts with a language magic command such as
# MAGIC `%sql` runs in that language instead, for that one cell only.
# MAGIC
# MAGIC The most important thing to understand about execution is that **cells share one
# MAGIC live session** on the attached compute. Variables, imports, function definitions,
# MAGIC temporary views, and widgets created in one cell are still visible in every other
# MAGIC cell afterward, regardless of which language created them. This is what makes
# MAGIC notebooks convenient for exploration, but it is also the single biggest source of
# MAGIC "works for me" bugs: if you run cells out of order, or rerun an earlier cell after
# MAGIC editing a later one, the live state can drift from what a clean top-to-bottom run
# MAGIC would produce. Re-running the whole notebook in order (**Run All**) is the only
# MAGIC way to be sure the result is reproducible - this comes up again in the best
# MAGIC practices and debugging sections.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Markdown Cells
# MAGIC
# MAGIC Markdown cells are useful for documentation. They render as formatted text as soon
# MAGIC as the cell runs (or as soon as you click out of it while editing), rather than
# MAGIC printing anything to an output area.
# MAGIC
# MAGIC You can create headings, lists, inline code, links, tables, and formatted
# MAGIC explanations - standard Markdown, plus inline LaTeX math between `$$` for anything
# MAGIC that needs a formula.
# MAGIC
# MAGIC ### Example heading
# MAGIC
# MAGIC - Bullet 1
# MAGIC - Bullet 2
# MAGIC - Bullet 3
# MAGIC
# MAGIC Inline code example: `print("hello")`
# MAGIC
# MAGIC Good notebooks read like a document with runnable examples embedded in it: a
# MAGIC reader should understand *why* a cell exists before they reach the code itself.

# COMMAND ----------

# 2. Basic Python Cell
#
# This cell has no magic command, so it runs in the notebook's default language
# (Python). Nothing here is displayed automatically - unlike a plain Python REPL,
# a notebook cell does not echo the value of its last expression, so you still
# need print() or display() to see a result.

print("Hello from Databricks!")
print("This is a Python code cell.")

# COMMAND ----------

# 3. Variables and Basic Logic

platform_name = "Databricks"
number_of_users = 5

print(f"Welcome to {platform_name}")
print(f"There are {number_of_users} users in this example")

if number_of_users > 3:
    print("We have more than 3 users")
else:
    print("We have 3 or fewer users")

# COMMAND ----------

# 4. Working with Lists

languages = ["Python", "SQL", "Scala", "R"]

for language in languages:
    print(f"Databricks supports {language}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Magic Commands
# MAGIC
# MAGIC Databricks notebooks support magic commands: a `%` token as the first thing in a
# MAGIC cell that changes how the rest of that cell is interpreted. A magic command only
# MAGIC affects the single cell it appears in - it does not change the notebook's default
# MAGIC language, and the next plain cell goes right back to running Python.
# MAGIC
# MAGIC Common examples:
# MAGIC
# MAGIC - `%python` - run Python code (rarely needed here, since Python is already the default)
# MAGIC - `%sql` - run SQL code against the current catalog and schema
# MAGIC - `%md` - write Markdown
# MAGIC - `%fs` - interact with the file system
# MAGIC - `%sh` - run shell commands on the driver node
# MAGIC
# MAGIC `02_magic_commands.py` in this same folder covers every magic command in depth,
# MAGIC including `%pip` and `%run`.
# MAGIC
# MAGIC One detail worth knowing early: a `%sql` cell shares the exact same Spark session
# MAGIC as the Python cells around it - same current catalog/schema, same temporary views,
# MAGIC same tables. It is a different *language* for that one cell, not a different
# MAGIC connection.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'Hello from SQL!' AS message;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Spark DataFrames
# MAGIC
# MAGIC Spark DataFrames are distributed tables: the data is partitioned across the
# MAGIC workers of the cluster, and operations on it run in parallel instead of on a
# MAGIC single machine. They are one of the main data structures used in Databricks.
# MAGIC
# MAGIC A detail that trips up people coming from pandas: most DataFrame operations
# MAGIC (`select`, `filter`, `groupBy`, `withColumn`, ...) are **transformations** - they
# MAGIC just build up a logical query plan and return immediately without touching any
# MAGIC data. Nothing actually runs on the cluster until an **action** is called, such as
# MAGIC `display()`, `count()`, `collect()`, or writing the DataFrame out. This "lazy
# MAGIC evaluation" is what lets Spark's optimizer look at the whole chain of
# MAGIC transformations and rewrite it into an efficient physical plan before running
# MAGIC anything - see `04_debugging_notebooks.py` for how to inspect that plan with
# MAGIC `EXPLAIN`.

# COMMAND ----------

# Create a simple Spark DataFrame

employee_data = [
    (1, "Alice", "Engineering", 75000),
    (2, "Bob", "Sales", 62000),
    (3, "Charlie", "Engineering", 82000),
    (4, "Diana", "Marketing", 68000),
    (5, "Eve", "Sales", 71000),
]

employee_columns = ["id", "name", "department", "salary"]

employees_df = spark.createDataFrame(employee_data, employee_columns)

display(employees_df)

# COMMAND ----------

# Select specific columns

display(employees_df.select("name", "department"))

# COMMAND ----------

# Filter rows

engineering_df = employees_df.filter(employees_df.department == "Engineering")

display(engineering_df)

# COMMAND ----------

# Group and aggregate data

department_salary_df = (
    employees_df
    .groupBy("department")
    .avg("salary")
)

display(department_salary_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Temporary SQL Views
# MAGIC
# MAGIC A temporary view lets you query a DataFrame using SQL. `createOrReplaceTempView`
# MAGIC registers the DataFrame under a name in the current Spark **session** - it is
# MAGIC visible to both `%sql` and Python cells in this same notebook (they share one
# MAGIC session, as noted above), but it is never written to storage and disappears the
# MAGIC moment the session ends (for example, when the cluster is detached or restarted).
# MAGIC It is not a Unity Catalog object and will not show up in Catalog Explorer.
# MAGIC
# MAGIC Two related tools worth knowing about:
# MAGIC
# MAGIC - `createOrReplaceGlobalTempView` - visible to *every* notebook attached to the
# MAGIC   same cluster, under the special `global_temp` database, instead of being scoped
# MAGIC   to just this notebook's session.
# MAGIC - A real Unity Catalog table or view (`CREATE TABLE` / `CREATE VIEW`) - persisted,
# MAGIC   governed, and visible to anyone with the right grants, from any cluster or SQL
# MAGIC   warehouse. See `02_introduction-to-unity-catalog/01_uc_introduction.py` for that
# MAGIC   workflow.

# COMMAND ----------

# Create a temporary SQL view

employees_df.createOrReplaceTempView("employees")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT *
# MAGIC FROM employees;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   department,
# MAGIC   COUNT(*) AS employee_count,
# MAGIC   AVG(salary) AS average_salary
# MAGIC FROM employees
# MAGIC GROUP BY department
# MAGIC ORDER BY average_salary DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Visualizations
# MAGIC
# MAGIC In Databricks, `display()` can show tables and visualizations.
# MAGIC
# MAGIC After running a cell with `display(...)`, use the visualization options in the
# MAGIC result area to switch between table, bar chart, line chart, pie chart, and scatter
# MAGIC plot - no extra plotting library required. For large results, `display()` renders
# MAGIC against a capped sample of rows rather than the full dataset, so it stays
# MAGIC responsive even over a huge DataFrame; if you need every row plotted (for example
# MAGIC with matplotlib), you must explicitly `collect()` or `toPandas()` first, which
# MAGIC pulls the full result to the driver and can fail if it does not fit in memory.

# COMMAND ----------

# Example visualization data

sales_data = [
    ("January", 12000),
    ("February", 15000),
    ("March", 18000),
    ("April", 14000),
    ("May", 22000),
]

sales_df = spark.createDataFrame(sales_data, ["month", "revenue"])

display(sales_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Notebook Widgets
# MAGIC
# MAGIC Widgets allow users to pass parameters into notebooks. They are useful for
# MAGIC reusable notebooks, dashboards, and scheduled jobs - the same notebook can run
# MAGIC against different departments, dates, or environments just by changing widget
# MAGIC values, with no code edits.
# MAGIC
# MAGIC Widgets always come in four flavors: `text` (free-form string), `dropdown` (pick
# MAGIC one value from a fixed list), `combobox` (pick from a list or type a custom
# MAGIC value), and `multiselect` (pick any number of values from a fixed list, returned
# MAGIC as one comma-separated string). `dbutils.widgets.get(...)` always returns a plain
# MAGIC string, regardless of which widget type produced it - a numeric widget value still
# MAGIC needs an explicit `int(...)`/`float(...)` conversion before arithmetic. Widgets
# MAGIC appear at the top of the notebook and persist across detach/reattach until
# MAGIC explicitly removed.
# MAGIC
# MAGIC `03_db_utilities.py` in this folder covers all four widget types and
# MAGIC `dbutils.notebook.run()` parameter passing in more depth.

# COMMAND ----------

# Create a text widget

dbutils.widgets.text("department", "Engineering", "Department")

# COMMAND ----------

# Read the widget value

selected_department = dbutils.widgets.get("department")

print(f"Selected department: {selected_department}")

# COMMAND ----------

# Use the widget value to filter data

filtered_df = employees_df.filter(employees_df.department == selected_department)

display(filtered_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Bonus: a dropdown widget
# MAGIC
# MAGIC A `dropdown` widget restricts the user to a fixed set of valid values, which is
# MAGIC often a better fit than free text for a field like seniority level - there is no
# MAGIC equivalent of "what happens if you type a value that doesn't exist" (question 4
# MAGIC below) because the UI simply will not let you enter one.

# COMMAND ----------

dbutils.widgets.dropdown(
    "seniority_level", "Mid", ["Junior", "Mid", "Senior"], "Seniority Level"
)

selected_seniority = dbutils.widgets.get("seniority_level")

print(f"Selected seniority level: {selected_seniority}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. File System Example
# MAGIC
# MAGIC Databricks provides `dbutils.fs` for interacting with storage. It is the Python
# MAGIC API version of the `%fs` magic command you will see in `02_magic_commands.py` -
# MAGIC the same underlying operations, but as real function calls you can use inside
# MAGIC loops, conditionals, and error handling, and that also work against Unity
# MAGIC Catalog **Volumes** (`/Volumes/catalog/schema/volume/...`), not just the legacy
# MAGIC DBFS root shown below. `03_db_utilities.py` goes much deeper into `dbutils.fs`,
# MAGIC including `cp`/`mv` and the built-in `help()`.
# MAGIC
# MAGIC Common commands:
# MAGIC
# MAGIC ```python
# MAGIC dbutils.fs.ls("/")
# MAGIC dbutils.fs.mkdirs("/tmp/example")
# MAGIC dbutils.fs.rm("/tmp/example", recurse=True)
# MAGIC ```

# COMMAND ----------

# List root folders

display(dbutils.fs.ls("/"))

# COMMAND ----------

# A minimal end-to-end example: create a scratch folder, write a file into it,
# list the folder to see the result, then remove it again. Using /tmp keeps this
# self-contained and safe to rerun - nothing here depends on a Unity Catalog volume
# already existing.

scratch_dir = "/tmp/databricks_intro/quickstart"

dbutils.fs.mkdirs(scratch_dir)
dbutils.fs.put(f"{scratch_dir}/note.txt", "Created from 01_introduction.py\n", overwrite=True)

display(dbutils.fs.ls(scratch_dir))

dbutils.fs.rm(scratch_dir, recurse=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Shell Command Example
# MAGIC
# MAGIC You can use `%sh` to run shell commands from a notebook cell. Unlike the Python
# MAGIC and SQL cells above, `%sh` does not run inside the Spark session at all - it opens
# MAGIC a plain OS subprocess **on the driver node only**. It cannot see DataFrames or
# MAGIC `dbutils`, and any file it writes lands on the driver's local disk rather than on
# MAGIC distributed storage, so it is invisible to worker nodes and to any other cluster.
# MAGIC It is well suited to one-off checks like confirming a library version or disk
# MAGIC space, not to data processing.

# COMMAND ----------

# MAGIC %sh
# MAGIC echo "Hello from the shell"
# MAGIC pwd

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Best Practices for Notebooks
# MAGIC
# MAGIC Good notebooks should be:
# MAGIC
# MAGIC - Clearly titled
# MAGIC - Split into logical sections
# MAGIC - Documented with Markdown
# MAGIC - Reproducible from top to bottom (Run All should give the same result every time)
# MAGIC - Parameterized when needed, using widgets rather than hardcoded values
# MAGIC - Free of hardcoded secrets - use `dbutils.secrets` instead (see `03_db_utilities.py`)
# MAGIC - Version controlled when used in real projects
# MAGIC
# MAGIC Avoid:
# MAGIC
# MAGIC - Very long cells
# MAGIC - Hidden assumptions
# MAGIC - Manual-only steps
# MAGIC - Unclear variable names
# MAGIC - Mixing unrelated experiments in one notebook
# MAGIC - Relying on cells being run out of order to "work" - if it only works because of
# MAGIC   leftover state from an earlier run, it will break the next time someone runs it
# MAGIC   from a clean session

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Mini Exercise
# MAGIC
# MAGIC Try changing the `department` widget value and rerun the filter cell.
# MAGIC
# MAGIC Questions:
# MAGIC
# MAGIC 1. Which employees are shown for `Engineering`?
# MAGIC 2. Which employees are shown for `Sales`?
# MAGIC 3. What happens if you enter a department that does not exist?
# MAGIC 4. Bonus: why can't question 3 happen with the `seniority_level` dropdown widget
# MAGIC    added above? What would change if it were a `combobox` instead?

# COMMAND ----------

# 14. Cleanup Example

# Uncomment these lines when you want to remove the widgets and the temp view:
# dbutils.widgets.remove("department")
# dbutils.widgets.remove("seniority_level")
# spark.catalog.dropTempView("employees")

print("Notebook completed successfully.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC
# MAGIC You learned:
# MAGIC
# MAGIC - how a notebook is structured into cells, and why shared session state makes
# MAGIC   top-to-bottom reproducibility something you have to protect deliberately
# MAGIC - how Markdown, Python, and SQL cells combine in one notebook
# MAGIC - how magic commands switch a single cell's language without changing the
# MAGIC   notebook's default
# MAGIC - how Spark DataFrames stay lazy until an action like `display()` or `count()`
# MAGIC   forces execution
# MAGIC - how temporary views expose a DataFrame to SQL for the lifetime of the session
# MAGIC - how `display()` renders interactive visualizations from a DataFrame
# MAGIC - how widgets parameterize a notebook, and the difference between the four
# MAGIC   widget types
# MAGIC - how `dbutils.fs` and `%sh` differ, and why `%sh` only sees the driver node
# MAGIC - notebook best practices, and habits to avoid
# MAGIC
# MAGIC Continue in this folder with:
# MAGIC
# MAGIC - `02_magic_commands.py` - every magic command in depth, including `%pip` and `%run`
# MAGIC - `03_db_utilities.py` - `dbutils.fs`, `dbutils.secrets`, widgets, and notebook workflows
# MAGIC - `04_debugging_notebooks.py` - the interactive Python debugger and debugging SQL
