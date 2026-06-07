---
icon: lucide/save
---

# Value Standardization & Write

The final steps for circuits: standardize some **column values** to title case, then
write the result to the silver table.

## Title-casing values with `initcap`

We want `circuit_name` and `locality` in title case (they're lowercase) for readable
downstream reports. Spark's `initcap` uppercases the first letter of each word.

Because we're replacing values in **existing** columns, use `withColumn` with the same
column name:

```python
circuits_final_df = (
    circuits_distinct_df
    .withColumn("circuit_name", F.initcap(F.col("circuit_name")))
    .withColumn("locality", F.initcap(F.col("locality")))
)
```

!!! note "`withColumn` replaces or adds"
    Passing an **existing** column name replaces its value; a **new** name adds a
    column. Here we replace.

## Writing to the silver table

Use the DataFrameWriter API, exactly as in bronze - Delta format, overwrite (full
refresh), saved to the `silver_table` three-level name:

```python
(
    circuits_final_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable(silver_table)
)
```

Verify with `display(spark.table(silver_table))` - the silver table now conforms to
our standards, with no data-quality issues. Run all cells to confirm the notebook
executes end-to-end without errors.

## Summary

We've completed the circuits silver transformation: read bronze → select columns →
standardize names → fix data quality → standardize values → write silver. The same
pattern applies to the remaining datasets.

## What's next

Next we apply the pattern to the races dataset. Continue to
[Transforming Races](07_races-data.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
