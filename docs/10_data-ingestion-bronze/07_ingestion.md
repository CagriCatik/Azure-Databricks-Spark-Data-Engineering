---
icon: lucide/flag-triangle-right
---

# Ingesting the Races File

With circuits done, we ingest the **races** dataset. Like circuits, it's a **CSV**
file, and the goal is the same: load it into a Delta table `races` in the `bronze`
schema.

!!! tip "Assignment"
    The races file follows the **exact same pattern** as circuits (read → schema →
    metadata → write). Try implementing it yourself first; the solution follows.

## Inspect the file

From **Catalog Explorer → landing → Files → races**, the file has five columns:

| Column | Type |
| --- | --- |
| `season` | integer |
| `round` | integer |
| `url` | string |
| `raceName` | string |
| `date` | date |
| `circuitId` | string |

## Solution

The easiest approach is to **clone the circuits notebook** and adjust it.

### Define the schema

```python
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DateType,
)

races_schema = StructType([
    StructField("season", IntegerType()),
    StructField("round", IntegerType()),
    StructField("url", StringType()),
    StructField("raceName", StringType()),
    StructField("date", DateType()),
    StructField("circuitId", StringType()),
])
```

### Read, add metadata, and write

Only the schema name and file name change versus circuits:

```python
races_df = (
    spark.read
    .format("csv")
    .option("header", True)
    .schema(races_schema)
    .load("/Volumes/formula1/landing/Files/races.csv")
)

races_final_df = (
    races_df
    .withColumn("ingestion_timestamp", F.current_timestamp())
    .withColumn("source_file", F.col("_metadata.file_path"))
)

(
    races_final_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("formula1.bronze.races")
)
```

The races data is now ingested into `bronze.races`, with the two metadata columns
added - `season`/`round` as integers, `date` as a date, the rest as strings.

## What's next

Both notebooks now look very similar with duplicated, hard-coded logic. Next we
refactor for production. Continue to
[Refactoring: Removing Hard-coded Values](08_remove-hardcoded-values.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
