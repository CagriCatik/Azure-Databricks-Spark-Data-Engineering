# Databricks notebook source
# MAGIC %md
# MAGIC # Databricks Magic Commands
# MAGIC
# MAGIC Magic commands allow you to change the behavior or language of a notebook cell.
# MAGIC A magic command is only recognized when it is the first token in the cell - it
# MAGIC applies to the whole cell, and only that cell.
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
# MAGIC A Databricks notebook has a single default language, set when the notebook is
# MAGIC created, but individual cells can override it for just that cell with a language
# MAGIC magic command.
# MAGIC
# MAGIC Common language magic commands:
# MAGIC
# MAGIC - `%python`
# MAGIC - `%sql`
# MAGIC - `%scala`
# MAGIC - `%r`
# MAGIC
# MAGIC All four run against the same attached cluster and the same Unity Catalog
# MAGIC catalog/schema context, so a `%sql` cell can immediately query a temp view a
# MAGIC Python cell just created, and vice versa. `%scala` and `%r` only work on compute
# MAGIC that supports those languages (a standard all-purpose cluster); a serverless SQL
# MAGIC warehouse, for example, only ever speaks SQL.
# MAGIC
# MAGIC The examples below use Python and SQL because they work in every Databricks
# MAGIC workspace.

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
# MAGIC `%fs` runs Databricks file system commands. Under the hood, `%fs <command> <args>`
# MAGIC is shorthand for the matching `dbutils.fs.<command>(<args>)` call - `%fs ls /` and
# MAGIC `dbutils.fs.ls("/")` list the exact same thing and hit the same underlying API.
# MAGIC
# MAGIC The trade-off is that `%fs` is a fixed, single-line magic syntax: great for quick,
# MAGIC ad hoc inspection of a folder, but it cannot be parameterized with a variable,
# MAGIC used inside a loop or an `if`, or wrapped in a `try`/`except`. As soon as you need
# MAGIC any of that - or you are scripting against a Unity Catalog **Volume** path
# MAGIC (`/Volumes/catalog/schema/volume/...`) as part of a larger pipeline rather than
# MAGIC eyeballing it - reach for `dbutils.fs` directly in a Python cell instead.
# MAGIC `03_db_utilities.py` in this folder is the deep dive on `dbutils.fs`.

# COMMAND ----------

# MAGIC %fs ls /

# COMMAND ----------

# MAGIC %fs ls /databricks-datasets/

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Shell Magic: `%sh`
# MAGIC
# MAGIC `%sh` runs shell commands on the driver node, in a plain OS subprocess that is
# MAGIC completely separate from the Spark session and from `dbutils` - it cannot see
# MAGIC DataFrames, temp views, or widgets. On a Unity Catalog cluster running in shared
# MAGIC access mode, `%sh` also executes with reduced privileges for isolation between
# MAGIC users on the same cluster, so some commands that would work on a dedicated
# MAGIC (single-user) cluster may be restricted there.
# MAGIC
# MAGIC Use this for lightweight environment checks.
# MAGIC
# MAGIC Avoid using `%sh` for production data workflows unless there is a clear reason -
# MAGIC anything it writes lands on the driver's local disk, not distributed storage, so
# MAGIC it disappears with the cluster and is never visible to worker nodes.

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
# MAGIC `%pip` installs Python packages into the notebook's environment, using the same
# MAGIC `pip` you would use locally. On Databricks, these installs are **notebook-scoped**:
# MAGIC they affect only the Python environment of the notebook that ran the command
# MAGIC (and any notebook it `%run`s), not other notebooks attached to the same cluster,
# MAGIC and not the cluster's own environment. That is different from **cluster-scoped
# MAGIC libraries** installed through the Libraries UI or an init script, which apply to
# MAGIC every notebook on the cluster and require the cluster itself to restart.
# MAGIC
# MAGIC Installing or upgrading a package with `%pip install` commonly triggers
# MAGIC Databricks to restart the notebook's **Python process** behind the scenes, so the
# MAGIC newly installed version is actually importable. That restart clears every
# MAGIC Python-level variable, import, and function defined so far - it does not touch
# MAGIC the Spark session itself, so temporary views, the current catalog/schema, and
# MAGIC widgets all survive. This is exactly why Databricks recommends putting `%pip
# MAGIC install` cells at the very top of a notebook: anything defined above one would
# MAGIC otherwise be wiped out and need to be rerun. If you want to force a clean Python
# MAGIC state on demand - for example after manually reloading a module - use the
# MAGIC `%restart_python` magic command rather than detaching and reattaching the whole
# MAGIC cluster.
# MAGIC
# MAGIC In real projects, prefer pinned versions, for example:
# MAGIC
# MAGIC ```python
# MAGIC %pip install faker==25.9.1
# MAGIC ```

# COMMAND ----------

# MAGIC %pip list

# COMMAND ----------

# MAGIC %md
# MAGIC ### Optional install example
# MAGIC
# MAGIC The commands below are shown as fenced code blocks rather than as a runnable
# MAGIC cell, so simply opening or running this notebook never changes the environment
# MAGIC on its own. Copy either one into a real cell only when you actually want to run
# MAGIC it.
# MAGIC
# MAGIC ```python
# MAGIC %pip install faker
# MAGIC ```
# MAGIC
# MAGIC If the install does not trigger an automatic restart, or you want a clean Python
# MAGIC state without detaching the cluster, follow it with:
# MAGIC
# MAGIC ```python
# MAGIC %restart_python
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Notebook Import Magic: `%run`
# MAGIC
# MAGIC `%run` executes another notebook **inline**, as if its cells were pasted directly
# MAGIC into the current notebook at that point. Every variable, function, import, and
# MAGIC temporary view the target notebook defines becomes directly available in the
# MAGIC calling notebook afterward, because both notebooks run in the very same Python
# MAGIC process and Spark session - there is no isolation between them. That is exactly
# MAGIC why the cells further down this notebook can reference `env`, `config`, and
# MAGIC `print_env_info()` once the `%run` cell below has executed: those names were
# MAGIC defined in `environment_variables_and_functions.py`, and `%run` merged them into
# MAGIC this notebook's namespace.
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
# MAGIC The imported notebook must exist at the referenced path, and the path is always
# MAGIC resolved relative to the *calling* notebook's folder, not the workspace root.
# MAGIC `%run` also has to be the only thing in its cell - it cannot be combined with
# MAGIC other Python code on the same line, and it cannot be called conditionally inside
# MAGIC an `if` block or a loop.

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
# MAGIC ### `%run` vs `dbutils.notebook.run()`
# MAGIC
# MAGIC These two look similar but behave very differently:
# MAGIC
# MAGIC | | `%run` | `dbutils.notebook.run()` |
# MAGIC | --- | --- | --- |
# MAGIC | Execution | Inline, in the *same* Python process and Spark session as the caller | An isolated notebook execution - its own REPL, like a small job run |
# MAGIC | Shared state | Full: variables, functions, imports, and temp views all become visible to the caller | None: the caller gets nothing back automatically |
# MAGIC | Return value | Nothing to return - everything defined is simply there afterward | A single string, from the child notebook's `dbutils.notebook.exit(value)` (empty string if it never calls `exit`) |
# MAGIC | Parameters | None - it just runs the cells as they are | A dictionary of parameters, which become widgets inside the child notebook |
# MAGIC | Typical use | Shared config/helpers the caller needs to use directly, like this folder's `environment_variables_and_functions.py` | Orchestrating independent notebooks as steps, without risking variable name collisions between them |
# MAGIC
# MAGIC A practical way to remember it: `%run` is for code you want to *become part of*
# MAGIC this notebook; `dbutils.notebook.run()` is for calling *another, independent*
# MAGIC notebook and getting a small result back - closer to calling a function that
# MAGIC happens to live in its own file. `03_db_utilities.py` in this folder has a full
# MAGIC working example.

# COMMAND ----------

# dbutils.notebook.run() launches the target notebook as an isolated run and only
# returns a string - it does not share variables back to this notebook the way
# %run does above. Uncomment to try it: environment_variables_and_functions.py
# never calls dbutils.notebook.exit(), so the result will just be an empty string.
#
# result = dbutils.notebook.run(
#     "./environment_variables_and_functions",
#     timeout_seconds=60,
#     arguments={"env": "test"},
# )
# print(f"Child notebook returned: {result!r}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Common Pitfalls
# MAGIC
# MAGIC - A magic command must be the first token in a cell - you cannot mix `%sql` and
# MAGIC   Python code in the same cell.
# MAGIC - Only one magic command governs a cell; you cannot stack two language magics.
# MAGIC - `%sh` starts a fresh subprocess per cell, so anything `export`-ed as an
# MAGIC   environment variable in one `%sh` cell is gone by the next `%sh` cell.
# MAGIC - `%pip install` cells belong at the top of the notebook, since the process
# MAGIC   restart they may trigger clears everything defined above them.
# MAGIC - `%run` shares state with the caller; `dbutils.notebook.run()` does not - pick
# MAGIC   the one that matches whether you want the callee's variables or just its
# MAGIC   result.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Summary
# MAGIC
# MAGIC Magic commands make notebooks more flexible.
# MAGIC
# MAGIC Recommended usage:
# MAGIC
# MAGIC - Use `%md` for documentation.
# MAGIC - Use `%sql` for readable SQL examples.
# MAGIC - Use `%fs` for quick filesystem checks; switch to `dbutils.fs` as soon as you
# MAGIC   need variables, loops, or error handling.
# MAGIC - Use `%sh` only when driver-node shell access is necessary.
# MAGIC - Use `%pip` carefully, prefer pinned versions, and expect a process restart.
# MAGIC - Use `%run` for small shared setup notebooks whose variables you want directly;
# MAGIC   use `dbutils.notebook.run()` when you want an isolated, independent run.
