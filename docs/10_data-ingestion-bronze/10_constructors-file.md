---
icon: lucide/wrench
---

# Ingesting Constructors (JSON + DDL Schema)

Next is the **constructors** dataset. Unlike circuits and races, it's a **JSON** file,
and we'll define its schema using a **DDL-formatted string** instead of `StructType`.

## Inspect the file

The Databricks UI doesn't syntax-highlight JSON, so it's easier to view JSON files in
the **Azure portal**. `constructors.json` is **single-line JSON** - each line is one
complete JSON object (one record):

```json
{"constructorId": "mclaren", "name": "McLaren", "nationality": "British", "url": "..."}
```

It's a flat structure (no nesting or arrays) with four string fields: `constructorId`,
`name`, `nationality`, `url`.

## Setup

In the notebook `03.Ingest Constructors File`, run the config and helper notebooks,
then define the source file and table name:

```python
%run ../00-common/01.environment-config
%run ../00-common/02.bronze-helpers

source_file = f"{landing_folder_path}/constructors.json"
table_name  = f"{catalog_name}.{bronze_schema}.constructors"
```

## Defining the schema (DDL-style)

A **DDL-formatted string** lists `column_name data_type` pairs - similar to Spark SQL
or Hive. Both this and `StructType` achieve the same result.

```python
constructors_schema = """
    constructorId STRING,
    name STRING,
    nationality STRING,
    url STRING
"""
```

!!! note "DDL vs StructType"
    The instructor's preference is `StructType`/`StructField` (it fits Python code
    well), but you may encounter the **DDL string** style in colleagues' projects, so
    it's worth knowing. Use `INT`, `DOUBLE`, etc. for non-string types. Triple quotes
    let you break it across lines.

## Read, add metadata, and write

Using the consistent `.format("json")` approach:

```python
constructors_df = (
    spark.read
    .format("json")
    .schema(constructors_schema)
    .option("mode", "failFast")
    .load(source_file)
)

constructors_final_df = add_ingestion_metadata(constructors_df)

constructors_final_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

`spark.read.json(...)` would also work, but `.format("json")` keeps the pattern
consistent. Verify with `display(spark.table(table_name))` - 214 records, all four
fields as strings, plus the two metadata columns.

## What's next

Next is a JSON file with a **nested** structure: drivers. Continue to
[Ingesting Drivers](11_drivers-file-ingestion.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
