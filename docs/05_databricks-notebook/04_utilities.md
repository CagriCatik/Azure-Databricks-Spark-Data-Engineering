---
icon: lucide/toolbox
---

# Databricks Utilities

Databricks utilities (`dbutils`) make it easier to **combine different types of tasks
in a single notebook** - for example, mixing file operations with ETL tasks.

!!! warning "Language support"
    Utilities can only be run from **Python, Scala, or R** cells. They **cannot** be
    run from a SQL cell.

## Commonly used utilities

| Utility | Purpose |
| --- | --- |
| **File system** (`dbutils.fs`) | Access the Databricks File System and perform file operations. Same capability as `%fs`, but more flexible/programmatic. |
| **Secrets** (`dbutils.secrets`) | Retrieve secret values from a **Secret Scope** backed by Databricks or **Azure Key Vault**. |
| **Widgets** (`dbutils.widgets`) | **Parameterize** notebooks so a calling notebook or app (e.g. an Azure Data Factory pipeline) can pass values at runtime - great for reusable notebooks. |
| **Notebook workflows** (`dbutils.notebook`) | Invoke one notebook from another and chain them. **No longer recommended** - use **Lakeflow Jobs** instead (easier to use and monitor). |

## `dbutils.fs` vs `%fs`

The `%fs` magic command uses the `dbutils.fs` package behind the scenes, so these are
equivalent:

```python
%fs ls /
```

```python
dbutils.fs.ls("/")
```

`dbutils.fs.ls` returns a **Python list**, which isn't very readable on its own. Wrap
it in the Databricks **`display`** command for a nicely formatted table:

```python
display(dbutils.fs.ls("/"))
```

!!! info "The `display` command"
    `display` is a Databricks command available only in **Python, Scala, and R**
    cells (not SQL). It renders data in a more readable, tabular format.

### Which should you use?

| Use case | Recommended |
| --- | --- |
| Quick, ad-hoc file system queries | `%fs` magic command |
| Programmatic tasks (process the output with code) | `dbutils.fs` |

## Example: combining utilities with Python

Because `dbutils.fs.ls` returns a list, you can process it with plain Python - for
example, counting files vs folders in `/databricks-datasets`:

```python
items = dbutils.fs.ls("/databricks-datasets")

folder_count = 0
file_count = 0
for item in items:
    if item.path.endswith("/"):
        folder_count += 1
    else:
        file_count += 1

print("Total folders:", folder_count)   # -> 53
print("Total files:", file_count)        # -> 2
```

Folders end with a trailing `/`; files do not. This shows how flexible utilities are
when combined with a language like Python, Scala, or R.

## Getting help on utilities

Rather than memorising every utility, use the built-in help:

```python
dbutils.help()            # list all available utilities
dbutils.fs.help()         # list methods of the file system utility
dbutils.fs.help("cp")     # detailed help + example for a specific method
```

- `dbutils.help()` lists all utilities (some marked experimental/preview, others
  generally available).
- `dbutils.fs.help()` lists the file system methods (mount helpers plus standard
  `cp`, `mv`, `rm`, etc.).
- Passing a method name returns a **description and an example**.

## What's next

Next we look at the notebook debugger. Continue to [Debugging Notebooks](05_debugging.md).

## References

- [Basic editing in Databricks notebooks](https://learn.microsoft.com/en-us/azure/databricks/notebooks/basic-editing)
- [Navigate the Databricks notebook and file editor](https://learn.microsoft.com/en-us/azure/databricks/notebooks/notebook-editor)
- [Run Databricks notebooks](https://learn.microsoft.com/en-us/azure/databricks/notebooks/run-notebook)
- [Databricks Utilities reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-utils)
- [Databricks widgets](https://learn.microsoft.com/en-us/azure/databricks/notebooks/widgets)
- [Secret management](https://learn.microsoft.com/en-us/azure/databricks/security/secrets/)
