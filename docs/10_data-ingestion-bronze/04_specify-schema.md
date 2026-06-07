---
icon: lucide/table-properties
---

# Specifying a Schema

By default, Spark reads CSV columns as **strings** unless schema inference or an explicit schema is used. This
lesson covers two ways to get correct types: **inferring** the schema and **defining**
it explicitly.

## Option 1: Infer the schema

```python
circuits_df = (
    spark.read
    .format("csv")
    .option("header", True)
    .option("inferSchema", True)   # note the capital S
    .load(source_path)
)
```

With `inferSchema` enabled, Spark scans the data, analyses each column's values, and
assigns appropriate types (e.g. `lat`/`lng` become `double`).

!!! warning "Inference has trade-offs"
    - It requires **scanning the data twice** (once to infer types, once to read).
    - The inferred schema **depends on the data** - if the data changes tomorrow, the
      schema may change too.

    Inference is great for **development and exploration**, but production workloads
    need **predictable** behaviour - so we define the schema explicitly.

## Option 2: Define the schema explicitly

Use `StructType` (the overall row structure) and `StructField` (each column):

```python
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType,
)

circuits_schema = StructType([
    StructField("circuitId", StringType()),
    StructField("circuitRef", StringType()),
    StructField("name", StringType()),
    StructField("location", StringType()),
    StructField("country", StringType()),
    StructField("lat", DoubleType()),
    StructField("lng", DoubleType()),
    StructField("alt", StringType()),
    StructField("url", StringType()),
])
```

Pass it to the reader with `.schema(...)` (and drop `inferSchema`):

```python
circuits_df = (
    spark.read
    .format("csv")
    .option("header", True)
    .schema(circuits_schema)
    .load(source_path)
)
```

!!! tip "Match the source column names"
    Use the exact incoming names - e.g. the longitude column is `lng`/`long` in the
    source, so keep it as-is. Explicit schemas keep the structure **controlled** and
    independent of the data received.

## Bonus: controlling bad records with read modes

Defining a schema lets you control how Spark handles malformed records via the `mode`
option:

| Mode | Behaviour |
| --- | --- |
| **`permissive`** *(default)* | Continue processing; unparseable values become `null`. |
| **`dropMalformed`** | Skip bad records and continue. |
| **`failFast`** | Immediately **fail the job** on any record that doesn't conform. |

```python
.option("mode", "failFast")
```

`failFast` is useful in controlled environments where you want the pipeline to **fail
loudly** rather than silently ignore bad data. For example, if you deliberately change
`country` to `DoubleType`, `failFast` raises a **malformed records** error, whereas
`permissive` would set `country` to `null`.

!!! note "Bronze vs silver validation"
    In the **bronze** layer we generally accept all incoming data and carry on, doing
    validations in the **silver** layer. (The demo uses `failFast` only to illustrate
    the behaviour, then reverts `country` to `StringType`.)

## What's next

Next we add ingestion metadata columns. Continue to
[Adding Ingestion Metadata](05_add-ingestion-metadata.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
