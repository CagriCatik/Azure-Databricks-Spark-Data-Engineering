---
icon: lucide/shield-alert
---

# Data Quality Checks

The bronze circuits data has two quality issues to fix before silver: records with a
**null `circuit_id`** and **duplicate records**.

## Filtering null business keys

`circuit_id` is the business key, so records without one are unusable for joins. Use
the `filter` method (alias: `where`). The condition can be a **SQL string** or a
**column expression**:

=== "SQL string"

    ```python
    circuits_valid_df = circuits_renamed_df.filter("circuit_id IS NOT NULL")
    ```

=== "Column expression"

    ```python
    circuits_valid_df = circuits_renamed_df.filter(
        F.col("circuit_id").isNotNull()
    )
    ```

!!! note "Python operators in column expressions"
    Use `==` (not `=`) for equality and `&` (not `and`) to combine conditions, e.g.
    `(F.col("age") > 3) & (F.col("name") == "Bob")`.

!!! tip "Recommendation"
    Both give the same result. For PySpark pipelines, **column expressions** are
    recommended - they're consistent with the DataFrame API and easier to read/debug
    as logic grows. (This removed the 2 null-key records, 82 → 80.)

## Removing duplicates

Two methods: `distinct()` and `dropDuplicates()`.

| Method | Behaviour |
| --- | --- |
| `distinct()` | Removes rows that are duplicates across **all** columns. |
| `dropDuplicates([cols])` | Removes duplicates based on the **given columns** (no args = same as `distinct`). |

```python
# distinct - whole-row duplicates
circuits_distinct_df = circuits_valid_df.distinct()

# dropDuplicates on the business key (preferred)
circuits_distinct_df = circuits_valid_df.dropDuplicates(["circuit_id"])
```

!!! warning "dropDuplicates picks other columns at random"
    When you dedupe on specific columns, the values of the **other** columns in the
    surviving row are chosen **non-deterministically** by Spark - you don't control
    which duplicate's values are kept.

!!! tip "Why dedupe on the business key?"
    In production you usually want **one row per business key**, even if other columns
    differ - you don't want duplicate keys in silver. So `dropDuplicates(["circuit_id"])`
    is more aligned with real-world practice than `distinct()`. (For exact duplicates,
    both give the same result - here 80 → 78.)

## What's next

Next we standardize column values and write to silver. Continue to
[Value Standardization & Write](06_data-standardisation-write.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
