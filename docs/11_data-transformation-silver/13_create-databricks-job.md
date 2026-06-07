---
icon: lucide/circle-plus
---

# Creating a Job

This lesson creates the Lakeflow Job and walks through the **job-level** configuration
(tasks come in the next lesson).

## Creating the job

1. Sidebar → **Jobs & Pipelines**.
2. Click the **Job** icon under *Create new*, or the **Create job** menu.
3. Rename the default name to something meaningful, e.g.
   **`job_formula1_lakehouse_full_refresh`**.

!!! tip "Naming matters"
    In production, use clear, consistent names that reflect the **scope and purpose**
    of the pipeline. This job does a full refresh of the Formula 1 lakehouse.

## Job details

| Setting | Notes |
| --- | --- |
| **Job ID** | Auto-assigned; use it to query system tables or interact via CLI/API. |
| **Creator / Run as** | Defaults to you. **In production, run as a service principal**, not an individual - otherwise the job fails when that user leaves. (Fine to leave as yourself for the demo.) |
| **Description** | Optional free text. |
| **Lineage** | Shows upstream/downstream tables used by the job (visible after a run). |
| **Performance optimization** | Faster compute startup and execution, at slightly higher cost; serverless only. |

## Schedules & triggers

Define how the job is triggered (default is **Manual**):

- **Cron schedule** - specific days/intervals.
- **File arrival** or **table update** events.
- **Continuous** - next run starts as one completes.

## Job parameters

Key-value pairs that pass **dynamic values** into tasks, making the pipeline flexible
and reusable - e.g. a `file_date` or `load_type` used across tasks and notebooks.

## Tags, notifications, permissions

| Setting | Purpose |
| --- | --- |
| **Tags** | Group jobs (and for billing). |
| **Notifications** | Alerts on start / success / failure / backlog / warning to email, Microsoft Teams, etc.; can include **metric thresholds** (e.g. notify if run duration exceeds 2 hours). |
| **Permissions** | Owner/admin plus added users with set permissions. |

## Advanced settings

| Setting | Behaviour |
| --- | --- |
| **Queue** | If resources (job/compute limits) are unavailable, wait up to **48 hours** for capacity before failing. Without queue, the job fails immediately on resource shortage. |
| **Max concurrent runs** | Allow more than one instance of the job to run at once - useful to catch up on backlogs (e.g. allow up to 3 concurrent runs). |

## What's next

Next we look at tasks - what they are and their properties. Continue to
[Tasks](14_tasks.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
