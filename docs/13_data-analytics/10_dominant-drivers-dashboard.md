---
icon: lucide/trophy
---

# Dominant Drivers Dashboard

This lesson visualizes the greatness-score query in a dashboard.

## Adding the dataset (from SQL)

Rather than a view, this demonstrates a **dataset from SQL**: in the dashboard's
**Data** tab, **create from SQL**, paste the greatness-score query, and **limit to 10
drivers** for a cleaner visual. Rename the dataset *Dominant Drivers*.

!!! tip
    In most cases a **view** is still preferable (centralized logic) — this just shows
    the inline-SQL dataset option.

## Building the page

Add a new page (*Dominant Drivers of All Time*) and a title text box, then three
visuals:

| Visual | Configuration |
| --- | --- |
| **Table** | Columns: greatness score, driver, wins, podiums, championships, race starts. |
| **Pie chart** | Angle = `total_championships`, color by `driver_name`, labels on (e.g. Schumacher & Hamilton 7 each → 16.67%). |
| **Bar chart** | Greatness score by driver, **sort by field**, *plasma* color ramp, labels on. |

The result clearly shows the dominant drivers — Hamilton and Schumacher at the top by
greatness score.

!!! tip "Explore further"
    Try other visualizations — e.g. a **scatter plot** to see the correlation between
    total podiums and greatness score.

## What's next

Next, the same analysis for teams (as an assignment). Continue to
[Dominant Teams Dashboard](11_build-dominant-teams-dashboard.md).

## References

- [SQL warehouse types](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/warehouse-types)
- [Dashboard concepts](https://learn.microsoft.com/en-us/azure/databricks/dashboards/concepts)
- [What is a Genie space?](https://learn.microsoft.com/en-us/azure/databricks/genie/)
- [Spark SQL window functions](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-window.html)
