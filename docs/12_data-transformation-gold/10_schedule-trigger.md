---
icon: lucide/calendar-clock
---

# Scheduled Trigger

In production you don't run jobs manually - they're triggered at regular intervals or
by events. This lesson covers **time-based scheduled** triggers.

## The trigger types

Add a trigger via **Add trigger**. The default is **None** (≈ manual). Databricks
offers four trigger types:

| Trigger | Fires when… |
| --- | --- |
| **Scheduled** | A time interval is reached (cron). |
| **File arrival** | A file appears in a monitored location. |
| **Table update** | A monitored Delta table is updated. |
| **Continuous** | Always keeps one active run (next starts as one completes). |

## Configuring a scheduled trigger

Select **Scheduled**. The trigger status can be **Active** or **Paused** (paused ≈ no
trigger). There are two modes:

| Mode | Capability |
| --- | --- |
| **Simple** | Run every N minutes/hours/days/weeks/months. |
| **Advanced** | Specific time + **time zone** (e.g. 15:52 daily, UTC). |

For example, set it to run at a specific time **every day**, then **Save**. The run
history then shows the **Launched** column as **By scheduler** (not Manually).

!!! warning "Watch the cost"
    An active schedule keeps running daily - on pay-as-you-go this incurs charges. You
    can **Pause** the trigger (and **Resume** later) or **delete** it when not needed.

## Cron syntax for complex schedules

The UI is limited - it can't express "9 AM and 11 AM daily" or "Mon & Fri only".
Behind the scenes Databricks Jobs uses **Quartz-style cron** syntax, which you can
enter directly.

```text
# Fields: seconds minutes hours day-of-month month day-of-week [year]

15 0 10 * * ?          # 10:15 AM every day
15 0 10 15 * ?         # 10:15 AM on the 15th of every month
15 0 10 ? * MON-FRI    # 10:15 AM every weekday (Mon–Fri)
```

!!! tip "Switching to cron"
    Pasting a cron expression disables the simple UI fields (you can't toggle back
    without clearing it). Read up on the Quartz cron fields so you can handle complex
    production scheduling requirements.

(The demo then **deletes** the trigger to avoid daily charges.)

## What's next

Next, event-based triggers - starting with file arrival. Continue to
[File Arrival Trigger](11_file-events-trigger.md).

## References

- [Spark SQL join syntax](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-join.html)
- [PySpark DataFrame.unionByName](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrame.unionByName.html)
- [Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/workflows/jobs/jobs)
- [Trigger jobs when new files arrive](https://learn.microsoft.com/en-us/azure/databricks/jobs/file-arrival-triggers)
- [Trigger jobs when source tables are updated](https://learn.microsoft.com/en-us/azure/databricks/jobs/trigger-table-update)
- [Job notifications](https://learn.microsoft.com/en-us/azure/databricks/jobs/notifications)
