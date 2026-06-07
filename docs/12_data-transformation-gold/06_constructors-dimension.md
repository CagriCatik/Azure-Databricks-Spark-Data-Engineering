---
icon: lucide/wrench
---

# Building the Constructors Dimension

The **`dim_constructors`** table needs `constructor_id`, `constructor_name`,
`nationality`, **and** a new **`nationality_region`** column that doesn't exist in
silver.

!!! info "Nationality region ≈ continent"
    Geographic attributes are common in warehouses so analysts can compare, e.g.,
    European vs American drivers. It's called *nationality region* (not *continent*)
    because we have **nationality**, not country. (Nationality ≈ country; nationality
    region ≈ continent.)

## The nationality-region reference table

In production you'd typically join to a **reference/lookup table** (country →
continent), perhaps sourced from a third party (e.g. World Bank). Here the
nationalities are awkward (e.g. *Argentine-Italian*), so the course **hard-codes** a
small mapping into a notebook and writes it to a Delta table:

```python
target_table = f"{catalog_name}.{gold_schema}.ref_nationality_region"
# DataFrame of (nationality, region) pairs, e.g.
#   British   -> Europe
#   American  -> North America
#   Brazilian -> South America
# ... written as a Delta table
```

## Building the dimension

Read the silver constructors table and the reference table, **join on `nationality`**,
select the columns, and write to `gold.dim_constructors`.

```python
%run ../00-common/01.environment-config
from pyspark.sql import functions as F

target_table = f"{catalog_name}.{gold_schema}.dim_constructors"

constructors_df = spark.table(f"{catalog_name}.{silver_schema}.constructors")
ref_nationality_region_df = spark.table(
    f"{catalog_name}.{gold_schema}.ref_nationality_region"
)

dim_constructors_df = constructors_df.join(
    ref_nationality_region_df,
    constructors_df.nationality == ref_nationality_region_df.nationality,
    "left",                       # left outer join
)
```

!!! tip "Why a left outer join?"
    The reference table is built by hand and may **miss** some nationalities. A
    **left** join keeps **all** constructor records - those with an unmapped
    nationality simply get a **null** region instead of being dropped.

Select and alias the columns (the model wants `nationality_region`, the reference has
`region`):

```python
dim_constructors_df = dim_constructors_df.select(
    constructors_df.constructor_id,
    constructors_df.constructor_name,
    constructors_df.nationality,
    ref_nationality_region_df.region.alias("nationality_region"),
)

dim_constructors_df.write.format("delta").mode("overwrite").saveAsTable(target_table)
```

!!! note "Remember `mode("overwrite")`"
    Set overwrite for a full refresh (and go back and add it to `dim_races` if you
    forgot it there).

## What's next

Next is the drivers dimension - nearly identical. Continue to
[Building the Drivers Dimension](07_drivers-dimension.md).

## References

- [Spark SQL join syntax](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html)
- [PySpark DataFrame.unionByName](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.unionByName.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Trigger jobs when new files arrive](https://learn.microsoft.com/en-us/azure/databricks/jobs/file-arrival-triggers)
- [Trigger jobs when source tables are updated](https://learn.microsoft.com/en-us/azure/databricks/jobs/trigger-table-update)
- [Job notifications](https://learn.microsoft.com/en-us/azure/databricks/jobs/notifications)
