---
icon: lucide/layout-dashboard
---

# Constructor Standings Dashboard

This dashboard is almost identical to the driver standings one — it uses the
`v_constructor_standings` view, swapping driver fields for constructor (team) fields.

!!! tip "Assignment"
    The requirements and visuals are the same as the driver dashboard. Try it
    yourself; the solution follows.

## Solution: clone and adapt

1. **Add data source** → `formula1.gold.v_constructor_standings`.
2. On the driver standings page, **Clone** it (three dots → Clone) and rename to
   *Constructor Championship Standings* — far quicker than rebuilding.

Then update each element to point at the constructor data:

| Element | Change |
| --- | --- |
| **Filter** | Remove the old field, add `season` from the constructor view; default `2025`, order descending. |
| **Table** | Retitle; change dataset to `v_constructor_standings`; replace `driver_name` with `constructor_name` (display name *Team*). |
| **Pie chart** | Change dataset; keep `number_of_wins`; replace `driver_name` with `constructor_name` in color & labels. |
| **Bar chart** | Retitle; change dataset; Y-axis → `constructor_name`. |

Filtering to 2025 shows McLaren champion (833 points), Mercedes 2nd (469), Red Bull
3rd (451) — matching the official team standings.

## What's next

Next we go beyond standings into a data-analyst's exploration of the most dominant
drivers. Continue to [Dominant Driver Analysis](09_dominant-driver-analysis-analysis.md).

## References

- [SQL warehouse types](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Dashboard concepts](https://learn.microsoft.com/en-us/azure/databricks/dashboards/concepts)
- [What is a Genie space?](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Spark SQL window functions](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
