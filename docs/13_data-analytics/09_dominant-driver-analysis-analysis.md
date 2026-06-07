---
icon: lucide/search
---

# Dominant Driver Analysis

A common question is: **who are the greatest drivers of all time?** This lesson takes
the journey of a **data analyst** — exploring the data step by step and validating as
we go, rather than jumping to conclusions. We use the **SQL Editor**.

## First attempt: total points

Aggregate the per-season driver standings view up to **per driver**:

```sql
SELECT driver_name, SUM(total_points) AS total_points
FROM formula1.gold.v_driver_standings
GROUP BY driver_name
ORDER BY total_points DESC;
```

This ranks Hamilton #1, Verstappen #2 — but **Michael Schumacher** (a 7-time champion)
appears ~10th, and legends like Prost and Senna rank even lower. The data looks wrong,
so points alone aren't a good measure.

## Adding more context

Bring in race starts, wins, podiums, and **championships** (derived: a `standing = 1`
in a season is a title):

```sql
SELECT
    driver_name,
    SUM(race_starts)                          AS race_starts,
    SUM(number_of_wins)                       AS total_wins,
    SUM(number_of_podiums)                    AS total_podiums,
    SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) AS total_championships
FROM formula1.gold.v_driver_standings
GROUP BY driver_name
ORDER BY total_championships DESC;
```

Visualizing total points vs championships (top 20) exposes the problem: drivers with
**zero wins** (e.g. Bottas, Leclerc, Perez) outrank Schumacher and Prost.

!!! info "Why points are misleading"
    The F1 **points system changed** over the decades (today 25 for a win; previously
    10, and even less earlier), and the **number of races per season** grew (24 today
    vs ~7–10 in the 1950s). So raw points unfairly penalize older drivers — points
    alone can't rank greatness.

## A "greatness score"

A better approach weights **achievements**. First, keep only drivers with at least one
championship using `HAVING`:

```sql
-- ... GROUP BY driver_name
HAVING SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) > 0
```

Then assign weighted scores (championships are hardest, so weighted highest) via a CTE:

```sql
WITH driver_metrics AS (
    SELECT
        driver_name,
        SUM(race_starts)                              AS race_starts,
        SUM(number_of_wins)                           AS total_wins,
        SUM(number_of_podiums)                        AS total_podiums,
        SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) AS total_championships
    FROM formula1.gold.v_driver_standings
    GROUP BY driver_name
    HAVING SUM(CASE WHEN standing = 1 THEN 1 ELSE 0 END) > 0
)
SELECT
    *,
    (total_championships * 100)
        + (total_wins * 10)
        + (total_podiums * 3)   AS greatness_score
FROM driver_metrics
ORDER BY greatness_score DESC;
```

| Achievement | Weight |
| --- | --- |
| Championship | 100 |
| Win | 10 |
| Podium | 3 |

This ranks Hamilton and Schumacher at the top, with Prost, Verstappen, Fangio, and
Senna appearing sensibly.

!!! note "A crude but reasonable model"
    These weights are a simple, hand-picked heuristic. A real analyst might use more
    sophisticated methods (e.g. percentiles). The point is to show **how an analyst
    iterates** toward a defensible metric — not to define the definitive ranking.

## What's next

Next we visualize this in a dashboard. Continue to
[Dominant Drivers Dashboard](10_dominant-drivers-dashboard.md).

## References

- [SQL warehouse types](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Dashboard concepts](https://learn.microsoft.com/en-us/azure/databricks/dashboards/concepts)
- [What is a Genie space?](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Spark SQL window functions](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
