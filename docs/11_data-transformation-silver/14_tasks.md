---
icon: lucide/list-tree
---

# Tasks

Tasks are where you spend most of your time with Lakeflow Jobs. This lesson covers the
task **types** and **properties**.

## Task categories

```mermaid
flowchart TB
    T[Task types]
    T --> Code[Code<br/>Notebook · Python script/wheel · JAR · spark-submit · Cleanroom]
    T --> SQL[SQL<br/>queries · .sql files · alerts on a SQL warehouse]
    T --> DT[Data transformation<br/>Lakeflow Spark Declarative Pipelines (ex-DLT) · dbt]
    T --> CF[Control flow<br/>if/else · for-each · trigger other jobs]
```

| Category | Examples |
| --- | --- |
| **Code** | Notebook, Python script, Python wheel, JAR, spark-submit, Cleanroom notebooks. |
| **SQL** | SQL queries, `.sql` files, query alerts (against a SQL warehouse). |
| **Data transformation** | Lakeflow Spark Declarative Pipelines (formerly **DLT**), **dbt**. |
| **Control flow** | `if/else` conditions, `for-each` loops, triggering other jobs. |

## Task properties

These apply to most task types (not control-flow tasks):

| Property | Description |
| --- | --- |
| **Source** | Location of the notebook/script - Databricks Workspace or **Git** repository, specified by path. |
| **Compute** | The environment to run on (see below). |
| **Dependencies** | Which tasks must run first (e.g. silver depends on bronze); supports multi-task dependencies. |
| **Libraries** | Dependent libraries from Workspace, ADLS, PyPI, Maven, etc. |
| **Task parameters** | Pass information between tasks for dynamic jobs. |
| **Retries** | Automatic retries for intermittent failures (e.g. network). |
| **Thresholds** | Flag tasks running longer than expected. |
| **Notifications** | Task-level alerts via email, Slack, etc. on completion/failure. |

## Compute: which to use?

| Task type | Compute |
| --- | --- |
| Control flow | Serverless capacity provided by Databricks |
| SQL | SQL warehouse |
| Other | Serverless (if enabled), all-purpose, or **jobs compute** |

!!! tip "Use jobs compute for Lakeflow Jobs"
    Between all-purpose and jobs compute, **jobs compute is recommended**:

    - **~50% cheaper** than all-purpose compute.
    - **Automatic cluster management** - Databricks starts it before the task and
      terminates it immediately after, minimizing resource usage.
    - **Workload isolation** - separates production from ad-hoc workloads for
      predictable performance.

## What's next

Next we create a second task and define dependencies. Continue to
[Task Dependencies](15_task-dependencies.md).

## References

- [PySpark DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html)
- [PySpark SQL functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Configure compute for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/compute)
