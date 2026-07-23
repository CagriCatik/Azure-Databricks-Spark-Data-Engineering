-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Build Constructor Standings
-- MAGIC
-- MAGIC #### Sources
-- MAGIC 1. fact_session_results
-- MAGIC 1. dim_constructors
-- MAGIC
-- MAGIC #### Output Columns
-- MAGIC 1. season
-- MAGIC 1. constructor id
-- MAGIC 1. constructor name
-- MAGIC 1. nationality
-- MAGIC 1. race starts
-- MAGIC 1. total points
-- MAGIC 1. number of wins
-- MAGIC 1. number of podiums
-- MAGIC 1. standing position
-- MAGIC
-- MAGIC #### Grain and ranking
-- MAGIC One row per `season` + `constructor_id`, aggregated across every
-- MAGIC `fact_session_results` row for that constructor in that season (race and
-- MAGIC sprint sessions alike, and across both of the constructor's drivers).
-- MAGIC `standing` is computed with
-- MAGIC `RANK() OVER (PARTITION BY season ORDER BY total_points DESC, number_of_wins DESC)`:
-- MAGIC constructors tied on both points and wins receive the same standing, and the
-- MAGIC position immediately after a tie is skipped by the number of tied rows
-- MAGIC (e.g. two constructors tied for 1st are both `standing = 1`, the next
-- MAGIC constructor is `standing = 3`) — the same convention used for real
-- MAGIC motorsport/sports league standings. `RANK()` is used deliberately instead of
-- MAGIC `ROW_NUMBER()` (which would arbitrarily break every tie) or `DENSE_RANK()`
-- MAGIC (which would not leave a gap after a tie).
-- MAGIC
-- MAGIC #### Why a view, not a table
-- MAGIC This is a `VIEW`, not a materialized table, so it always reflects whatever
-- MAGIC is currently in gold with zero extra orchestration: as soon as
-- MAGIC `fact_session_results` is merged with a new batch, the next query against
-- MAGIC this view picks up the change immediately, with no separate refresh step
-- MAGIC and no risk of the standings drifting out of sync with the fact/dimension
-- MAGIC tables underneath. Re-aggregating on every query is cheap at Formula 1's
-- MAGIC data volume (tens of thousands of result rows, not big data), so there is no
-- MAGIC practical reason to trade that always-fresh guarantee for a materialized
-- MAGIC table that would need its own incremental refresh logic.

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC #### Entity Relationship Diagram - Formula1 Gold Schema
-- MAGIC
-- MAGIC ![Formula1 Gold Data.png](../../z-course-images/formula1-gold-data-erd.png "Formula1 Gold Data.png")

-- COMMAND ----------

CREATE OR REPLACE VIEW formula1_incr.gold.v_constructor_standing
AS
WITH constructor_session_summary
AS
  (SELECT r.season,
        c.constructor_id,
        c.constructor_name,
        c.nationality,
        COUNT(*) AS race_starts,
        SUM(r.points) AS total_points,
        COUNT_IF(r.is_win) AS number_of_wins,
        COUNT_IF(r.is_podium) AS number_of_podiums
    FROM formula1_incr.gold.fact_session_results r
    JOIN formula1_incr.gold.dim_constructors c
      ON r.constructor_id = c.constructor_id
  GROUP BY r.season,
        c.constructor_id,
        c.constructor_name,
        c.nationality)
SELECT season,
       constructor_id,
       constructor_name,
       nationality,
       RANK() OVER (PARTITION BY season ORDER BY total_points DESC, number_of_wins DESC) AS standing,
       race_starts,
       total_points,
       number_of_wins,
       number_of_podiums
  FROM constructor_session_summary;


-- COMMAND ----------

-- MAGIC %md
-- MAGIC #### Validation - spot check the current season's standings

-- COMMAND ----------

SELECT * FROM formula1_incr.gold.v_constructor_standing WHERE season = 2025