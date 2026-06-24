# Databricks notebook source
# MAGIC %md
# MAGIC # Debugging Databricks Notebooks
# MAGIC
# MAGIC Databricks supports interactive debugging for Python notebooks.
# MAGIC
# MAGIC > Enable debugger: **Settings → Developer → Enable Python notebook interactive debugger**
# MAGIC
# MAGIC Requirements:
# MAGIC
# MAGIC - Databricks Runtime 13.3 LTS or higher
# MAGIC - Python notebooks
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
# MAGIC - Step through the code line by line.
# MAGIC - Watch how `tax`, `item_price_with_tax`, and `final_price` change.

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
# MAGIC - Use **Step In** when the function is called.
# MAGIC - Use **Step Out** after inspecting the function internals.

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
# MAGIC Use the debugger to inspect the variable values.

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
# MAGIC ## Demo 5: Defensive Checks
# MAGIC
# MAGIC Assertions can catch incorrect assumptions early.

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
# MAGIC
# MAGIC A reliable notebook should be reproducible after clearing state and running all cells in order.
