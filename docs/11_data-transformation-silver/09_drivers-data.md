---
icon: lucide/users
---

# Transforming Drivers

The **drivers** dataset has primary key `driverId` plus `name`, `dob`, `nationality`,
`url`, and the two metadata columns. The key difference: **`name` is a struct** with
`forename` and `surname` - we'll flatten it into a single `driver_name`.

## Requirements

| # | Requirement |
| --- | --- |
| 1 | Read the bronze drivers table. |
| 2 | Drop the `url` column. |
| 3 | Standardize names (`driverId` → `driver_id`, `dob` → `date_of_birth`). |
| 4 | **Concatenate `name.forename` + `name.surname`** into `driver_name`, title-cased. |
| 5 | Remove duplicates (on `driver_id`). |
| 6 | Title-case `nationality`. |
| 7 | Write to the silver drivers table. |

## Flattening the nested name

Use `withColumn` to add a new column, and `concat_ws` (concatenate with separator) to
join the nested fields with a space. Reference nested fields with dot notation
(`name.forename`):

```python
drivers_concatenated_df = drivers_renamed_df.withColumn(
    "driver_name",
    F.initcap(
        F.concat_ws(" ", F.col("name.forename"), F.col("name.surname"))
    ),
)
```

`initcap` title-cases the concatenated value.

## Dropping the original `name` struct

After creating `driver_name`, the original `name` struct is redundant. You can chain a
`drop` directly - a sensible place to chain transformations:

```python
drivers_concatenated_df = (
    drivers_renamed_df
    .withColumn(
        "driver_name",
        F.initcap(F.concat_ws(" ", F.col("name.forename"), F.col("name.surname"))),
    )
    .drop("name")
)
```

!!! tip "Chain transformations when it makes sense"
    The course generally uses one transformation per step (clear, easy to debug), but
    chaining is fine **when it improves readability** - like adding `driver_name` then
    dropping `name` together. Avoid over-chaining, which makes code hard to read.

## Remaining steps

```python
# Dedupe on the primary key
drivers_distinct_df = drivers_concatenated_df.dropDuplicates(["driver_id"])

# Title-case nationality
drivers_final_df = drivers_distinct_df.withColumn(
    "nationality", F.initcap(F.col("nationality"))
)

drivers_final_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
```

The silver drivers table now has a flat `driver_name` (title-cased), `date_of_birth`,
title-cased `nationality`, and the metadata columns - the nested struct is gone.

## What's next

Next is the more complex results dataset, where we explore Spark **coding styles**.
Continue to [Transforming Results](10_results-data.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
