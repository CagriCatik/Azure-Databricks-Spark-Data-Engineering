---
icon: lucide/trophy
---

# Dominant Teams Dashboard

The final analysis applies the same greatness-score approach to **constructors
(teams)**.

!!! tip "Assignment"
    Use the **same algorithm** as the drivers (championships × 100 + wins × 10 +
    podiums × 3). For teams, two drivers race per team, so points/wins roughly double —
    but the same scoring works. Try it yourself; the solution follows.

## Solution: clone and adapt

1. **Clone** the dominant drivers query → *Dominant Constructors*, changing every
   `driver` reference to `constructor` and reading from `v_constructor_standings`
   instead of `v_driver_standings`.

   ```sql
   WITH constructor_metrics AS (
       SELECT
           constructor_name,
           SUM(race_starts)                              AS race_starts,
           SUM(number_of_wins)                           AS total_wins,
           SUM(number_of_podiums)                        AS total_podiums,
           SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) AS total_championships
       FROM formula1.gold.v_constructor_standings
       GROUP BY constructor_name
       HAVING SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) > 0
   )
   SELECT
       *,
       (total_championships * 100) + (total_wins * 10) + (total_podiums * 3)
           AS greatness_score
   FROM constructor_metrics
   ORDER BY greatness_score DESC;
   ```

2. Create a **dataset from SQL** (top 10), rename *Dominant Constructors*.
3. **Clone** the dominant drivers dashboard page and swap the dataset and
   `driver_name` → `constructor_name` (display name *Team*) in the table, pie chart,
   and bar chart.

The results: **Ferrari** dominates (22 championships, far ahead), then McLaren and
Williams. Note Red Bull (6 titles) outranks Williams (9 titles) on greatness score
because Red Bull has far more **wins** — a nuance the weighted score captures.

## Section complete

You've used the **SQL Editor** to analyze data and **dashboards** to visualize the
outcomes — turning the lakehouse's curated data into clear insights about the most
dominant drivers and teams.

## What's next

Finally, querying data with natural language. Continue to [AI/BI Genie](12_ai-bi-genie.md).

## References

- [SQL warehouse types](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Dashboard concepts](https://learn.microsoft.com/en-us/azure/databricks/dashboards/concepts)
- [What is a Genie space?](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Spark SQL window functions](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
