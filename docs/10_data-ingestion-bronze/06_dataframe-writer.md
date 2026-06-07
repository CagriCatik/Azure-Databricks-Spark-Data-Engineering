---
icon: lucide/save
---

# Writing Data: DataFrameWriter

The final step is to write the prepared DataFrame to a Delta table in the bronze
schema, using the **DataFrameWriter** API (`.write`, the counterpart to `.read`).

## Writing the table

```python
(
    circuits_final_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("formula1.bronze.circuits")
)
```

| Part | Meaning |
| --- | --- |
| `.format("delta")` | The format. Delta is the **default** and recommended format (transactional guarantees, reliability) - explicit here for clarity. |
| `.mode("overwrite")` | Whether to **append** or **overwrite**. We overwrite because we're doing a **full load** - every run replaces all data. (Incremental logic comes later.) |
| `.saveAsTable("catalog.schema.table")` | Save as a table in Unity Catalog using the three-level name `formula1.bronze.circuits`. |

## Verifying the data

=== "SQL"

    ```sql
    %sql
    SELECT * FROM formula1.bronze.circuits;
    ```

=== "PySpark"

    ```python
    display(spark.table("formula1.bronze.circuits"))
    ```

`spark.table(...)` reads a table into a DataFrame, which `display()` then visualizes.
Both confirm the data was written, including the two metadata columns.

You can also browse **Catalog Explorer → bronze → circuits** to see the structure and
sample data (attach to a compute to query it).

## Summary

We've ingested the circuits data from landing into the bronze layer as a Delta table,
establishing the **read → schema → metadata → write** pattern we'll reuse for every
other dataset.

## What's next

Next we apply the pattern to the races dataset. Continue to
[Ingesting the Races File](07_ingestion.md).

## References

- [Spark CSV data source options](https://spark.apache.org/docs/latest/sql-data-sources-csv.html)
- [PySpark DataFrameReader](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameReader.html)
- [PySpark DataFrameWriter](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.html)
- [File metadata column](https://learn.microsoft.com/en-us/azure/databricks/ingestion/file-metadata-column)
- [What are tables in Azure Databricks?](https://learn.microsoft.com/en-us/azure/databricks/tables/table-overview)
