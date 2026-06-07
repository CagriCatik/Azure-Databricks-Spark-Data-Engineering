---
icon: lucide/pencil-line
---

# Standardizing Column Names

This lesson renames columns to **snake_case** and makes them more meaningful (e.g.
`lat` → `latitude`, `lng` → `longitude`).

## Ways to rename

| Approach | Notes |
| --- | --- |
| `.alias()` on a column expression | Rename within a `select` (seen previously). |
| `withColumnRenamed(old, new)` | Rename **one** column in place; returns a DataFrame. |
| `withColumnsRenamed({...})` | Rename **multiple** columns via a dict (Spark **3.4+**). |

!!! note "`withColumn` vs `withColumnRenamed`"
    `withColumn` **adds** a new column; `withColumnRenamed` simply **renames** an
    existing one in place (no new column).

## Renaming one at a time

```python
circuits_renamed_df = (
    circuits_selected_df
    .withColumnRenamed("circuitId", "circuit_id")
    .withColumnRenamed("name", "circuit_name")
    .withColumnRenamed("lat", "latitude")
    .withColumnRenamed("lng", "longitude")
)
```

## Renaming multiple columns at once (preferred)

Spark 3.4+ offers `withColumnsRenamed`, which takes a dictionary - cleaner and more
readable:

```python
circuits_renamed_df = circuits_selected_df.withColumnsRenamed({
    "circuitId": "circuit_id",
    "name": "circuit_name",
    "lat": "latitude",
    "lng": "longitude",
})
```

!!! tip "Recommendation"
    On Spark **3.4 or later** (the modern Databricks runtime), use
    `withColumnsRenamed` - it's more concise and improves readability. On older
    environments, use multiple `withColumnRenamed` calls. The course uses
    `withColumnsRenamed`.

## What's next

Next we fix data-quality issues (null keys and duplicates). Continue to
[Data Quality Checks](05_data-quality-checks.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
