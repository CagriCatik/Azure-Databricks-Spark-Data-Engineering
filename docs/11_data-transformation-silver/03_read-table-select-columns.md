---
icon: lucide/table-2
---

# Reading & Selecting Columns

This lesson reads the bronze circuits table and selects only the required columns. The
notebooks live in a new `03-silver` folder (e.g. `01.Transform Circuits Data`, Python,
attached to the cluster).

## Configuration

As with bronze, avoid hard-coding catalog/schema names - `%run` the config notebook
and build table-name variables with f-strings:

```python
%run ../00-common/01.environment-config

bronze_table = f"{catalog_name}.{bronze_schema}.circuits"
silver_table = f"{catalog_name}.{silver_schema}.circuits"
```

## Reading a table: two methods

| Method | Notes |
| --- | --- |
| `spark.read.table(name)` | Part of the **DataFrameReader** API - allows chaining read options. |
| `spark.table(name)` | Concise SparkSession method - no extra options. |

```python
circuits_df = spark.table(bronze_table)
display(circuits_df)
```

!!! info "When to use which?"
    `spark.read.table` lets you chain options such as **time travel**:

    ```python
    circuits_df = spark.read.option("versionAsOf", 0).table(bronze_table)
    ```

    `spark.table` doesn't offer that flexibility. Since we don't need extra options
    here, **`spark.table`** is recommended - simpler and concise.

## Selecting required columns

We need to drop `url`. Two ways: **select** the columns you want (this lesson), or
**drop** the unwanted column (shown later). `select` takes columns as **strings** or
**column expressions**:

=== "Column strings"

    ```python
    circuits_selected_df = circuits_df.select(
        "circuitId", "circuitRef", "name", "location",
        "country", "lat", "lng", "alt",
    )
    ```

=== "Column expressions"

    ```python
    from pyspark.sql import functions as F

    circuits_selected_df = circuits_df.select(
        F.col("circuitId"),
        F.col("circuitRef"),
        F.col("name"),
        F.col("location"),
        F.col("country").alias("country_name"),   # rename
        F.upper(F.col("country")),                 # transform values
        # ...
    )
    ```

When you pass strings, Spark converts them to column expressions internally. Using
`F.col(...)` explicitly gives more flexibility - you can `.alias()` to rename or apply
functions like `F.upper()` inline.

!!! note "Recommendation"
    Column expressions are more flexible, so the course uses them going forward.

## What's next

Next we standardize the column names. Continue to
[Standardizing Column Names](04_column-standardisation.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
