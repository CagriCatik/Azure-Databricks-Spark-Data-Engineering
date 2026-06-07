---
icon: lucide/flag-triangle-right
---

# Transforming Races

Next is the **races** dataset (`02.Transform Races Data`). The bronze table has seven
data columns plus the two metadata columns (nine total). Its primary key is a
**composite key**: `season` + `round`. `circuitId` is a foreign key to circuits.

## Requirements

Very similar to circuits, with one key difference (deduplication uses the composite
key):

| # | Requirement |
| --- | --- |
| 1 | Read the bronze races table. |
| 2 | Drop the `url` column. |
| 3 | Standardize names to snake_case (`raceName` → `race_name`, `circuitId` → `circuit_id`), and rename `date` → `race_date`. |
| 4 | **Remove duplicates on the composite key** (`season` + `round`). |
| 5 | Title-case `race_name`. |
| 6 | Write to the silver races table. |

!!! tip "Assignment"
    The pattern is the same as circuits except for the composite-key dedupe - try it
    yourself first; the solution follows.

## Solution

```python
%run ../00-common/01.environment-config
from pyspark.sql import functions as F

bronze_table = f"{catalog_name}.{bronze_schema}.races"
silver_table = f"{catalog_name}.{silver_schema}.races"

races_df = spark.table(bronze_table)

# Select required columns (drop url)
races_selected_df = races_df.select(
    "season", "round", "raceName", "date", "circuitId",
    "ingestion_timestamp", "source_file",
)

# Standardize names
races_renamed_df = races_selected_df.withColumnsRenamed({
    "raceName": "race_name",
    "circuitId": "circuit_id",
    "date": "race_date",
})

# Deduplicate on the COMPOSITE key
races_valid_df = races_renamed_df.dropDuplicates(["season", "round"])

# Title-case race name
races_final_df = races_valid_df.withColumn(
    "race_name", F.initcap(F.col("race_name"))
)

races_final_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
```

!!! note "Composite-key dedupe"
    Unlike circuits (single key), pass **both** key columns to `dropDuplicates`:
    `["season", "round"]`. (Here this removed 5 duplicates, 1,178 → 1,173.)

The silver races table now has `race_name` in title case, `race_date`, `circuit_id`,
and the two metadata columns.

## What's next

Next is the constructors dataset, where we'll use `drop` instead of `select`. Continue
to [Transforming Constructors](08_constructors-data.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
