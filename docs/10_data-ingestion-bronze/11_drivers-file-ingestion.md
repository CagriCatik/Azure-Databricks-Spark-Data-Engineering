---
icon: lucide/users
---

# Ingesting Drivers (Nested JSON)

The **drivers** dataset is also JSON, but it contains a **nested structure**, which
makes it more interesting.

## Inspect the file

`drivers.json` is single-line JSON (one record per line). Most fields are simple
(`driverId`, `dob`, `nationality`, `url`), but **`name`** is a **complex type** - a
struct with two nested fields:

```json
{"driverId": "hamilton", "name": {"forename": "Lewis", "surname": "Hamilton"}, ...}
```

!!! note "Preserve structure in bronze"
    In the bronze layer the goal is **not** to flatten or transform - we won't combine
    `forename` and `surname` into one field. We read the data **as-is**, but correctly,
    preserving the nested structure.

## Defining a nested schema

Define the **inner** schema (for `name`) first, then reference it as the data type of
the `name` field in the **outer** schema:

```python
from pyspark.sql.types import (
    StructType, StructField, StringType, DateType,
)

name_schema = StructType([
    StructField("forename", StringType()),
    StructField("surname", StringType()),
])

driver_schema = StructType([
    StructField("driverId", StringType()),
    StructField("name", name_schema),       # <- nested struct, not StringType
    StructField("dob", DateType()),
    StructField("nationality", StringType()),
    StructField("url", StringType()),
])
```

The only difference for complex types: the field's data type is the **inner schema**
rather than a primitive type.

## Read, add metadata, and write

```python
drivers_df = (
    spark.read
    .format("json")
    .schema(driver_schema)
    .load(source_file)
)

drivers_final_df = add_ingestion_metadata(drivers_df)

drivers_final_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

Inspecting the DataFrame, `name` is a **struct** containing `forename` and `surname` -
the nested structure is preserved through to the Delta table, alongside the metadata
columns.

## What's next

Next we read a dataset split across **multiple files** in a folder: results. Continue
to [Ingesting Results](12_results-file-ingestion.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
