---
icon: lucide/wrench
---

# Transforming Constructors

The **constructors** dataset is simple: primary key `constructorId`, plus `name`,
`nationality`, `url`, and the two metadata columns. The requirements mirror races, with
one twist - we use the **`drop`** method instead of `select`.

## Requirements

| # | Requirement |
| --- | --- |
| 1 | Read the bronze constructors table. |
| 2 | **Drop the `url` column** (using `drop`, not `select`). |
| 3 | Standardize names: `constructorId` → `constructor_id`, `name` → `constructor_name`. |
| 4 | Remove duplicates (none exist, but add the logic for future-proofing). |
| 5 | Title-case `nationality`. |
| 6 | Write to the silver constructors table. |

## Dropping a column

`drop` returns a new DataFrame **without** the specified column(s) - the inverse of
`select`. Columns can be strings or expressions.

```python
constructors_dropped_df = constructors_df.drop("url")
```

## Solution

```python
%run ../00-common/01.environment-config
from pyspark.sql import functions as F

bronze_table = f"{catalog_name}.{bronze_schema}.constructors"
silver_table = f"{catalog_name}.{silver_schema}.constructors"

constructors_df = spark.table(bronze_table)

# Drop unwanted column
constructors_dropped_df = constructors_df.drop("url")

# Standardize names
constructors_renamed_df = constructors_dropped_df.withColumnsRenamed({
    "constructorId": "constructor_id",
    "name": "constructor_name",
})

# Dedupe on the primary key (future-proofing)
constructors_distinct_df = constructors_renamed_df.dropDuplicates(["constructor_id"])

# Title-case nationality
constructors_final_df = constructors_distinct_df.withColumn(
    "nationality", F.initcap(F.col("nationality"))
)

constructors_final_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
```

!!! note "`select` vs `drop`"
    Use **`select`** to keep a few columns and drop many; use **`drop`** to remove a
    few columns and keep many. This dataset has no duplicates, but the
    `dropDuplicates(["constructor_id"])` step future-proofs the notebook.

## What's next

Next is the drivers dataset, which has a **nested** `name` struct to flatten. Continue
to [Transforming Drivers](09_drivers-data.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
