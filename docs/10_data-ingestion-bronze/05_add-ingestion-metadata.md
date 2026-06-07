---
icon: lucide/tags
---

# Adding Ingestion Metadata

Before writing to bronze, we add two metadata columns: **source file** and **ingestion
timestamp**. In production pipelines this improves traceability and helps with auditing
and debugging.

## `withColumn` and DataFrame immutability

To add a column, use `withColumn(name, expression)`. It returns a **new DataFrame** -
Spark DataFrames are **immutable**, so transformations don't change the original; you
assign the result to a new variable.

## Ingestion timestamp

```python
from pyspark.sql import functions as F

circuits_final_df = circuits_df.withColumn(
    "ingestion_timestamp", F.current_timestamp()
)
```

- Import the built-in functions module, aliased as `F`, to access functions.
- `F.current_timestamp()` is the timestamp at which the **job runs** (not a file
  timestamp).

## Source file name

Databricks exposes a special **`_metadata`** column when reading files, containing
information about the file being read - including `file_path`.

```python
circuits_final_df = (
    circuits_df
    .withColumn("ingestion_timestamp", F.current_timestamp())
    .withColumn("source_file", F.col("_metadata.file_path"))
)
```

- `_metadata.file_path` gives the full file path.
- Because it's a column reference (not a literal), wrap it with `F.col(...)`.

The result includes the full path, e.g.
`/Volumes/formula1/landing/Files/circuits.csv`.

!!! tip "Why source file matters"
    For single files it's not a big deal, but **results** and **sprints** arrive as
    folders with many files - knowing which file a record came from is very useful.

## What's next

With metadata added, the final step is writing to bronze. Continue to
[Writing Data: DataFrameWriter](06_dataframe-writer.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
