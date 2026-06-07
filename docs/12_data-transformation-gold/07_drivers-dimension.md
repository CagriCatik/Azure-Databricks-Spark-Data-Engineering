---
icon: lucide/users
---

# Building the Drivers Dimension

The **`dim_drivers`** table is built almost exactly like the constructors dimension.

## Requirements

1. Read `silver.drivers` and `gold.ref_nationality_region`.
2. **Left outer join** on `nationality`.
3. Select `driver_id`, `driver_name`, `date_of_birth`, `nationality`, and the
   reference `region` **aliased** to `nationality_region`.
4. Write to `gold.dim_drivers`.

!!! tip "Assignment"
    This mirrors the constructors dimension - try it yourself first; the solution
    follows.

## Solution

```python
%run ../00-common/01.environment-config
from pyspark.sql import functions as F

target_table = f"{catalog_name}.{gold_schema}.dim_drivers"

drivers_df = spark.table(f"{catalog_name}.{silver_schema}.drivers")
ref_nationality_region_df = spark.table(
    f"{catalog_name}.{gold_schema}.ref_nationality_region"
)

dim_drivers_df = drivers_df.join(
    ref_nationality_region_df,
    drivers_df.nationality == ref_nationality_region_df.nationality,
    "left",
).select(
    drivers_df.driver_id,
    drivers_df.driver_name,
    drivers_df.date_of_birth,
    drivers_df.nationality,
    ref_nationality_region_df.region.alias("nationality_region"),
)

dim_drivers_df.write.format("delta").mode("overwrite").saveAsTable(target_table)
```

`gold.dim_drivers` now holds each driver's name, date of birth, nationality, and
nationality region.

## What's next

With all three dimensions built, next is the central fact table. Continue to
[Building the Results Fact Table](08_results-fact.md).

## References

- [Spark SQL join syntax](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html)
- [PySpark DataFrame.unionByName](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.unionByName.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Trigger jobs when new files arrive](https://learn.microsoft.com/en-us/azure/databricks/jobs/file-arrival-triggers)
- [Trigger jobs when source tables are updated](https://learn.microsoft.com/en-us/azure/databricks/jobs/trigger-table-update)
- [Job notifications](https://learn.microsoft.com/en-us/azure/databricks/jobs/notifications)
