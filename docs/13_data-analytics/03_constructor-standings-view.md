---
icon: lucide/medal
---

# Constructor Standings View

The **constructor standings** view is almost identical to the driver standings — just
grouped by **constructor** (team) instead of driver.

| | Driver standings | Constructor standings |
| --- | --- | --- |
| Dimension | `dim_drivers` | `dim_constructors` |
| Identity columns | `driver_id`, `driver_name` | `constructor_id`, `constructor_name` |

!!! tip "Assignment"
    The requirements mirror the driver standings — try it yourself first; the solution
    follows.

## Reading large SQL

!!! tip "Read from the inside out"
    With large SQL statements, don't read top-down — **start from the innermost part**
    (the join + aggregation in the CTE) and work outward to the ranking.

## Solution

```sql
CREATE OR REPLACE VIEW formula1.gold.v_constructor_standings AS
WITH constructor_session_summary AS (
    SELECT
        r.season,
        c.constructor_id,
        c.constructor_name,
        c.nationality,
        COUNT(*)              AS race_starts,
        SUM(r.points)         AS total_points,
        COUNT_IF(r.is_win)    AS number_of_wins,
        COUNT_IF(r.is_podium) AS number_of_podiums
    FROM formula1.gold.fact_session_results r
    INNER JOIN formula1.gold.dim_constructors c
        ON r.constructor_id = c.constructor_id
    GROUP BY r.season, c.constructor_id, c.constructor_name, c.nationality
)
SELECT
    *,
    RANK() OVER (
        PARTITION BY season
        ORDER BY total_points DESC, number_of_wins DESC
    ) AS standing
FROM constructor_session_summary;
```

The aggregation joins `fact_session_results` to `dim_constructors` on `constructor_id`,
computes the per-season-per-constructor metrics, and the outer query ranks teams
within each season.

Filtering to 2025 matches the official team standings — McLaren champion with 833
points, Mercedes 2nd, Red Bull 3rd.

## What's next

Next we introduce Databricks SQL — the analytics environment. Continue to
[Introduction to Databricks SQL](04_sql_intro.md).

## References

- [SQL warehouse types](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Dashboard concepts](https://learn.microsoft.com/en-us/azure/databricks/dashboards/concepts)
- [What is a Genie space?](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Spark SQL window functions](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
