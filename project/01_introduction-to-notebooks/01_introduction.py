# Databricks notebook source
# MAGIC %md
# MAGIC # Introduction to Databricks Notebooks
# MAGIC
# MAGIC Databricks notebooks combine **documentation**, **code**, **SQL**, **visualizations**, and **collaboration** in one place.
# MAGIC
# MAGIC In this notebook we will cover:
# MAGIC
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
# MAGIC ## 1. Markdown Cells
# MAGIC
# MAGIC Markdown cells are useful for documentation.
# MAGIC
# MAGIC You can create headings, lists, inline code, links, and formatted explanations.
# MAGIC
# MAGIC ### Example heading
# MAGIC
# MAGIC - Bullet 1
# MAGIC - Bullet 2
# MAGIC - Bullet 3
# MAGIC
# MAGIC Inline code example: `print("hello")`

# COMMAND ----------

# 2. Basic Python Cell

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
# MAGIC Databricks notebooks support magic commands.
# MAGIC
# MAGIC Common examples:
# MAGIC
# MAGIC - `%python` run Python code
# MAGIC - `%sql` run SQL code
# MAGIC - `%md` write Markdown
# MAGIC - `%fs` interact with the file system
# MAGIC - `%sh` run shell commands

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'Hello from SQL!' AS message;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Spark DataFrames
# MAGIC
# MAGIC Spark DataFrames are distributed tables. They are one of the main data structures used in Databricks.

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
# MAGIC A temporary view lets you query a DataFrame using SQL.

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
# MAGIC After running a cell with `display(...)`, use the visualization options in the result area to switch between table, bar chart, line chart, pie chart, and scatter plot.

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
# MAGIC Widgets allow users to pass parameters into notebooks. They are useful for reusable notebooks, dashboards, and scheduled jobs.

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
# MAGIC ## 10. File System Example
# MAGIC
# MAGIC Databricks provides `dbutils.fs` for interacting with storage.
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

# MAGIC %md
# MAGIC ## 11. Shell Command Example
# MAGIC
# MAGIC You can use `%sh` to run shell commands from a notebook cell.

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
# MAGIC - Reproducible from top to bottom
# MAGIC - Parameterized when needed
# MAGIC - Free of hardcoded secrets
# MAGIC - Version controlled when used in real projects
# MAGIC
# MAGIC Avoid:
# MAGIC
# MAGIC - Very long cells
# MAGIC - Hidden assumptions
# MAGIC - Manual-only steps
# MAGIC - Unclear variable names
# MAGIC - Mixing unrelated experiments in one notebook

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

# COMMAND ----------

# 14. Cleanup Example

# Uncomment this line when you want to remove the widget:
# dbutils.widgets.remove("department")

print("Notebook completed successfully.")