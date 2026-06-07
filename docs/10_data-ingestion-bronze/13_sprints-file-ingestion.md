---
icon: lucide/timer
---

# Ingesting Sprints (Multi-line JSON)

The final dataset is **sprints**. Like results, it's stored in a **folder** of files -
but with one important difference: the JSON is in **multi-line** format.

## Single-line vs multi-line JSON

The `sprints` folder has **five** files (2021–2025) - sprint races were only introduced
in 2021.

| | Previous JSON files | Sprints |
| --- | --- | --- |
| Format | **Line-delimited** - each line is one complete record | **Multi-line** - one record spans many lines |

```json
{
  "season": 2024,
  "round": 5,
  "raceName": "...",
  "results": "..."
}
```

!!! warning "Spark must be told"
    By default Spark treats **each line** as a separate JSON object. For multi-line
    JSON this causes errors, because a record spans multiple lines. You must explicitly
    enable the **`multiLine`** option.

## Reading multi-line JSON

The only new thing is the `multiLine` option (note the **uppercase `L`**):

```python
%run ../00-common/01.environment-config
%run ../00-common/02.bronze-helpers

source_file = f"{landing_folder_path}/sprints"     # folder
table_name  = f"{catalog_name}.{bronze_schema}.sprints"

sprints_df = (
    spark.read
    .format("json")
    .schema(sprints_schema)
    .option("multiLine", True)        # <- read multi-line JSON records
    .load(source_file)
)

sprints_final_df = add_ingestion_metadata(sprints_df)

sprints_final_df.write.format("delta").mode("overwrite").saveAsTable(table_name)
```

The schema and the rest of the logic are the same as the results file. Verify all
seasons loaded:

```sql
%sql
SELECT season, COUNT(*) AS records
FROM formula1.bronze.sprints
GROUP BY season
ORDER BY season;
```

This shows data for all five seasons (2021–2025).

## Section complete

All six datasets are now ingested into the bronze layer as Delta tables:

| Dataset | Format | Notes |
| --- | --- | --- |
| circuits, races | CSV | `header` + explicit schema |
| constructors | single-line JSON | DDL-string schema |
| drivers | single-line JSON | nested struct schema |
| results | single-line JSON | folder of files |
| sprints | **multi-line** JSON | folder of files + `multiLine` option |

The bronze layer is ready for transformation into silver.

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
