---
icon: lucide/timer
---

# Transforming Sprints

The final dataset is **sprints**. Structurally it's **identical** to results - same
four-part composite key (`season`, `round`, `constructorId`, `driverId`) and the same
columns. The only difference is the content: sprint race results instead of main race
results. Like results, it has **duplicates** and **null primary keys** to handle.

!!! tip "Assignment"
    The requirements are exactly the same as results. Implement it using your preferred
    style (step-by-step, chained, or middle ground) - just ensure the logic is correct
    and the **key validations** (null keys + duplicates) are handled. The solution
    follows.

## Solution (middle ground)

Using the same balanced approach as results:

```python
%run ../00-common/01.environment-config
from pyspark.sql import functions as F

bronze_table = f"{catalog_name}.{bronze_schema}.sprints"
silver_table = f"{catalog_name}.{silver_schema}.sprints"

# Group 1: read + shape
sprints_df = (
    spark.table(bronze_table)
    .select(...)                       # drop url
    .withColumnsRenamed({...})
)

# Group 2: data quality (null keys + duplicates)
sprints_valid_df = (
    sprints_df
    .filter(
        F.col("season").isNotNull() & F.col("round").isNotNull() &
        F.col("constructor_id").isNotNull() & F.col("driver_id").isNotNull()
    )
    .dropDuplicates(["season", "round", "constructor_id", "driver_id"])
)

# Group 3: value transforms
sprints_final_df = sprints_valid_df.withColumn(
    "race_name", F.initcap(F.col("race_name"))
)

# Write
sprints_final_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
```

## Section complete

All six datasets are now transformed into the silver layer:

| Dataset | Notable transformation |
| --- | --- |
| circuits | single-key dedupe, null-key filter, title-case |
| races | **composite-key** dedupe (`season`+`round`) |
| constructors | used `drop` instead of `select` |
| drivers | **flattened nested** `name` struct via `concat_ws` |
| results | explored coding styles; **4-part composite key** quality checks |
| sprints | same shape as results |

!!! note "Style recommendation"
    A balanced, **logically grouped** approach is preferred in production - clear,
    easy to debug, and concise. Conciseness should never come at the cost of
    readability and maintainability.

The silver layer is ready for building the **gold** layer.

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
