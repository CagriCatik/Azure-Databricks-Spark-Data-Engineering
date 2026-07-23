# Databricks notebook source
# MAGIC %md
# MAGIC # Debugging Databricks Notebooks
# MAGIC
# MAGIC Databricks supports interactive, step-through debugging for Python notebooks -
# MAGIC the same breakpoint-based workflow you would get from an IDE, running directly
# MAGIC against the live cluster your notebook is already attached to.
# MAGIC
# MAGIC > Enable debugger: **Settings -> Developer -> Enable Python notebook interactive debugger**
# MAGIC
# MAGIC Requirements:
# MAGIC
# MAGIC - Databricks Runtime 13.3 LTS or higher - the debugger depends on execution
# MAGIC   infrastructure that only exists in the notebook kernel from that runtime
# MAGIC   onward, so the menu option has no effect on an older runtime
# MAGIC - Python notebooks only - SQL, Scala, and R cells are not steppable
# MAGIC - The setting is per-user, and the compute you attach to must also support it,
# MAGIC   so enabling it once does not carry over to a cluster running an older runtime
# MAGIC
# MAGIC Once a breakpoint is hit, execution pauses on the live cluster and these actions
# MAGIC become available:
# MAGIC
# MAGIC - **Breakpoint** - click the gutter next to a line number (or call the built-in
# MAGIC   `breakpoint()`) to mark a line where execution should pause, right before that
# MAGIC   line runs.
# MAGIC - **Continue** - resume normal execution until the next breakpoint, or the end
# MAGIC   of the cell.
# MAGIC - **Step Over** - run the current line and pause at the next line in the *same*
# MAGIC   function. If the current line calls a function, the whole function runs to
# MAGIC   completion without pausing inside it.
# MAGIC - **Step In** - if the current line calls a function, pause at the first line
# MAGIC   *inside* that function instead of running over it, so you can watch its
# MAGIC   internals.
# MAGIC - **Step Out** - run the rest of the current function until it returns, then
# MAGIC   pause back in the caller, right after the call - the inverse of Step In,
# MAGIC   useful once you have seen enough of a function's internals.
# MAGIC - **Variable inspection** - a panel showing every local and global variable in
# MAGIC   the currently paused frame, updated live as you step.
# MAGIC - **Debug console** - lets you evaluate arbitrary expressions in the paused
# MAGIC   frame's scope (print a variable, call a helper, check a condition) without
# MAGIC   editing the cell itself.
# MAGIC
# MAGIC This notebook contains small examples for practicing:
# MAGIC
# MAGIC 1. Breakpoints
# MAGIC 2. Step over
# MAGIC 3. Step in
# MAGIC 4. Step out
# MAGIC 5. Variable inspection
# MAGIC 6. Debug console usage

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo 1: Debugging a Simple Calculation
# MAGIC
# MAGIC Goal:
# MAGIC
# MAGIC - Set a breakpoint on the first assignment.
# MAGIC - Step through the code line by line with **Step Over**.
# MAGIC - Watch how `tax`, `item_price_with_tax`, and `final_price` change in the
# MAGIC   variable inspection panel as each line runs.

# COMMAND ----------

# Calculate the final price of an item and print that value

item_price = 120.00
tax_rate = 20        # Given as percentage
discount = 10.00

# 1. Calculate the tax to be applied
tax = item_price * (tax_rate / 100)

# 2. Apply tax to the item price
item_price_with_tax = item_price + tax

# 3. Apply the flat discount to the item price
final_price = item_price_with_tax - discount

# Print the final price
print(f"Final Price: {final_price:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo 2: Step In and Step Out
# MAGIC
# MAGIC Goal:
# MAGIC
# MAGIC - Set a breakpoint inside `calculate_final_price`.
# MAGIC - Use **Step In** when the function is called, to watch its internals.
# MAGIC - Use **Step Out** after inspecting the function internals, to jump straight
# MAGIC   back to the caller instead of stepping over every remaining line one by one -
# MAGIC   this matters even more once a function has a loop inside it.

# COMMAND ----------

def calculate_final_price(item_price, tax_rate, discount):
    """Calculate the final price after tax and discount."""

    # 1. Calculate the tax to be applied
    tax = item_price * (tax_rate / 100)

    # 2. Apply tax to the item price
    item_price_with_tax = item_price + tax

    # 3. Apply the flat discount to the item price
    final_price = item_price_with_tax - discount

    return final_price

# COMMAND ----------

# Main program

item_price = 120.00
tax_rate = 20        # Given as percentage
discount = 10.00

final_price = calculate_final_price(item_price, tax_rate, discount)

print(f"Final Price: {final_price:.2f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo 3: Finding a Bug
# MAGIC
# MAGIC The next example contains a logic bug.
# MAGIC
# MAGIC Expected behavior:
# MAGIC
# MAGIC - If quantity is 3
# MAGIC - And unit price is 50
# MAGIC - The subtotal should be 150
# MAGIC
# MAGIC Use the debugger to inspect the variable values. Pausing right after the buggy
# MAGIC line and checking `subtotal` in the variable inspection panel shows the wrong
# MAGIC value (53) immediately - often faster than adding a `print()` and rerunning the
# MAGIC whole cell.

# COMMAND ----------

quantity = 3
unit_price = 50

# Bug: this should multiply, not add
subtotal = quantity + unit_price

print(f"Subtotal: {subtotal}")

# COMMAND ----------

# Corrected version

quantity = 3
unit_price = 50

subtotal = quantity * unit_price

print(f"Correct subtotal: {subtotal}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo 4: Debugging with DataFrames
# MAGIC
# MAGIC Debugging DataFrames often means checking:
# MAGIC
# MAGIC - Schema
# MAGIC - Row counts
# MAGIC - Intermediate DataFrames
# MAGIC - Filter conditions

# COMMAND ----------

orders_data = [
    (1, "Alice", 120.00, "completed"),
    (2, "Bob", 80.00, "pending"),
    (3, "Charlie", 150.00, "completed"),
    (4, "Diana", 50.00, "cancelled"),
]

orders_df = spark.createDataFrame(
    orders_data,
    ["order_id", "customer_name", "amount", "status"]
)

orders_df.printSchema()
display(orders_df)

# COMMAND ----------

completed_orders_df = orders_df.filter(orders_df.status == "completed")

print(f"Completed order count: {completed_orders_df.count()}")

display(completed_orders_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Demo 4b: Debugging SQL with `EXPLAIN`
# MAGIC
# MAGIC Stepping through Python line by line does not help when the problem (or the slow
# MAGIC part) is inside a Spark SQL query's execution plan - for example, a filter that
# MAGIC silently is not pushed down to the data source, or a join that shuffles far more
# MAGIC data than expected. For that, "debugging" means reading the query plan instead of
# MAGIC stepping through code.
# MAGIC
# MAGIC `EXPLAIN` (in SQL) and `.explain()` (on a DataFrame) print the plan Spark's
# MAGIC optimizer produced without actually running the query. Reading it bottom to top:
# MAGIC the bottom shows how data is scanned and filtered, and each level above it shows
# MAGIC the next transformation - a `PushedFilters` entry near the scan confirms a filter
# MAGIC made it all the way down to the read, instead of being applied only after
# MAGIC everything was loaded.

# COMMAND ----------

completed_orders_df.createOrReplaceTempView("orders_view")

# COMMAND ----------

# MAGIC %sql
# MAGIC EXPLAIN SELECT * FROM orders_view WHERE status = 'completed';

# COMMAND ----------

# The equivalent Python DataFrame API call - useful when the query is built up
# programmatically instead of typed out as a SQL string.
completed_orders_df.explain()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demo 5: Defensive Checks
# MAGIC
# MAGIC Assertions can catch incorrect assumptions early.
# MAGIC
# MAGIC A caveat worth knowing: `assert` is a debugging and development tool for
# MAGIC catching *programmer* errors and invariants, not a substitute for real input
# MAGIC validation in production code. Python's `-O` optimization flag strips `assert`
# MAGIC statements out entirely, so code that relies on `assert` to reject bad *user*
# MAGIC input can silently stop validating anything under that flag. For checks that must
# MAGIC always run, raise an explicit exception (`raise ValueError(...)`) instead.

# COMMAND ----------

def calculate_discounted_price(price, discount):
    """Return price after a flat discount."""

    assert price >= 0, "Price must not be negative"
    assert discount >= 0, "Discount must not be negative"
    assert discount <= price, "Discount must not be greater than price"

    return price - discount

# COMMAND ----------

valid_price = calculate_discounted_price(100, 15)

print(f"Valid discounted price: {valid_price}")

# COMMAND ----------

# Uncomment to see the assertion fail:
#
# invalid_price = calculate_discounted_price(100, 120)
# print(invalid_price)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Debugging Checklist
# MAGIC
# MAGIC Use this checklist when a notebook behaves unexpectedly:
# MAGIC
# MAGIC 1. Run the notebook from top to bottom.
# MAGIC 2. Check that previous cells were executed.
# MAGIC 3. Inspect variable values near the failing cell.
# MAGIC 4. Check DataFrame schemas and row counts.
# MAGIC 5. Isolate the smallest reproducible example.
# MAGIC 6. Avoid relying on hidden state from old runs.
# MAGIC 7. Restart the Python process if state becomes confusing.
# MAGIC 8. Use the interactive debugger for stepping through Python logic; use
# MAGIC    `EXPLAIN` / `.explain()` for SQL and DataFrame logic or performance questions.
# MAGIC 9. Check the cluster's Spark UI (Stages and SQL/DataFrame tabs) when a job is
# MAGIC    slow or stuck, rather than only staring at notebook output.
# MAGIC
# MAGIC A reliable notebook should be reproducible after clearing state and running all
# MAGIC cells in order.
