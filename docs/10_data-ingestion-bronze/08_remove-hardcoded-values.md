---
icon: lucide/settings
---

# Refactoring: Removing Hard-coded Values

The circuits and races notebooks are very similar, with **duplication** and
**hard-coded values** (landing path, catalog name, schema name) - not ideal for
production. This lesson centralizes configuration.

## The problem with hard-coding

Hard-coded values make it hard to switch environments. Moving from development to
production might change the file folder path, catalog name, or schema name - forcing
you to edit **every** ingestion notebook.

!!! tip "Solution: a shared config notebook"
    Store these values in one **configuration notebook** and `%run` it from every
    ingestion notebook. When something changes, you update one file.

## Create the configuration notebook

In a new `00-common` folder, create `01.environment-config` (Python):

```python
# Unity Catalog object names
catalog_name = "formula1"
bronze_schema = "bronze"
silver_schema = "silver"
gold_schema = "gold"

# Source files land in this volume
landing_folder_path = "/Volumes/formula1/landing/Files"
```

!!! note "Why variables for schema names?"
    In an enterprise project, schema names may differ per environment (e.g.
    `dev_bronze`, `test_bronze`). Centralizing them means you change one value when
    promoting between environments. (Remember the **uppercase `V`** in `/Volumes`.)

You don't run this notebook directly - it's executed **from** the ingestion notebooks.

## Use the config from an ingestion notebook

Run the config notebook with a **relative** `%run` path (the ingestion notebooks are
in `02-bronze`, so go up one level to `00-common`):

```python
%run ../00-common/01.environment-config
```

The variables (e.g. `catalog_name`) are now available. Build the file and table names
from them using **f-strings**:

```python
source_file = f"{landing_folder_path}/circuits.csv"
table_name  = f"{catalog_name}.{bronze_schema}.circuits"
```

Then use the variables in the reader and writer:

```python
circuits_df = spark.read.format("csv").option("header", True) \
    .schema(circuits_schema).load(source_file)

circuits_final_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

`table_name` resolves to `formula1.bronze.circuits`. Only the file name (`circuits.csv`)
and table name (`circuits`) remain specific to this notebook; everything else comes
from the config.

!!! tip "Remove display statements for production"
    `display(...)` calls are handy while learning but **unnecessary in production** -
    remove them before deploying. (You can use `display(spark.table(table_name))` to
    verify, then delete it.)

Apply the same changes to the races notebook (using `races.csv` and the `races` table
name).

## What's next

Next we remove the duplicated metadata logic with a helper function. Continue to
[Refactoring: Extracting Helper Functions](09_handle-repeated-logic.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
