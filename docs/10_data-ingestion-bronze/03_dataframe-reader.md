---
icon: lucide/book-open-text
---

# Reading Data: DataFrameReader

This lesson uses the **DataFrameReader** API to read the `circuits.csv` file into a
Spark DataFrame.

## Setup

In **Workspace → databricks-course → formula1-project**, create a `02-bronze` folder
for the ingestion notebooks, and a notebook `01.Ingest Circuits File` with **Python**
as the default language. Attach it to the **Databricks Course Cluster**.

!!! tip "Inspect the file first"
    Before coding, view the file via **Catalog → formula1 → landing → Files volume →
    `circuits.csv`**. It's a simple CSV with seven columns and a handful of records.

## The SparkSession entry point

`SparkSession` is the entry point into Spark. In Databricks it's created automatically
and available as the `spark` variable. `spark.read` returns a **DataFrameReader**,
which loads data from sources such as CSV, JSON, Parquet, and Delta.

## Two ways to read a CSV

| Method | Example |
| --- | --- |
| **Convenience method** | `spark.read.csv(path)` |
| **`.format()` method** | `spark.read.format("csv").load(path)` |

`spark.read.csv(...)` is a convenience wrapper around `.format("csv")`. Likewise
`spark.read.json(...)` ≡ `.format("json")`.

!!! note "We use `.format()`"
    `.format()` is a more general pattern that keeps syntax consistent across CSV,
    JSON, Parquet, etc. - useful in this multi-format project.

## Reading the file

```python
circuits_df = (
    spark.read
    .format("csv")
    .option("header", True)
    .load("/Volumes/formula1/landing/Files/circuits.csv")
)
```

!!! tip "Insert the path from the Catalog"
    Browse **Catalog → formula1 → landing → Files → circuits**, and use the
    double-arrow icon to insert the file path into your notebook.

## Viewing the data

```python
circuits_df.show()        # prints first 20 rows (pass a number for more)
display(circuits_df)      # Databricks tabular visualization (nicer)
```

- `show()` prints the first 20 rows to the console but **truncates** long values
  (you can pass `truncate=False`).
- `display()` is the Databricks visualization command - much nicer tabular output, and
  what you'll mostly use.

## Fixing the header

Without options, the column names come out as `_c0`, `_c1`, … and the real header is
read as the first data row. The `header` option fixes this:

```python
.option("header", True)   # treat the first line as column names (default: False)
```

After setting `header` to `True`, the columns become `circuitId`, `url`,
`circuitName`, etc.

!!! warning "Data types are still all strings"
    Even with the header fixed, **every column is read as a string** - even `lat` and
    `lng` which contain decimals. Spark does not infer CSV column types unless schema inference is enabled. The next
    lesson fixes this.

## What's next

Next we control data types by specifying a schema. Continue to
[Specifying a Schema](04_specify-schema.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
