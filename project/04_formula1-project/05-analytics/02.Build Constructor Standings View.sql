-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Build Constructor Standings
-- MAGIC
-- MAGIC Reporting view: aggregates the `fact_session_results` fact table up to
-- MAGIC one row per season + constructor, joined against the `dim_constructors`
-- MAGIC dimension for descriptive attributes (name, nationality), and ranks
-- MAGIC constructors within each season by points. Same rollup pattern as
-- MAGIC `v_driver_standing` - a fine-grained fact table (one row per driver per
-- MAGIC session per race) summarized to the grain a constructor standings report
-- MAGIC needs (one row per constructor per season).
-- MAGIC
-- MAGIC Implemented as a `VIEW`, not a materialized table, for the same reason as
-- MAGIC the driver standings: cheap to compute on demand, and always reflects
-- MAGIC the latest fact/dimension data with nothing to rebuild or fall out of
-- MAGIC sync.
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

-- COMMAND ----------

-- MAGIC %md
-- MAGIC
-- MAGIC #### Entity Relationship Diagram - Formula1 Gold Schema
-- MAGIC
-- MAGIC ![Formula1 Gold Data.png](../../z-course-images/formula1-gold-data-erd.png "Formula1 Gold Data.png")

-- COMMAND ----------

-- One row per season + constructor: aggregate the fact table (grain = one
-- row per driver, per session, per race) up to a season summary before
-- ranking. Note: fact_session_results holds both RACE and SPRINT session
-- rows, so COUNT(*)/SUM(points) below total across both session types.
CREATE OR REPLACE VIEW formula1.gold.v_constructor_standing
AS
WITH constructor_session_summary
AS
  (SELECT r.season,
        c.constructor_id,
        c.constructor_name,
        c.nationality,
        COUNT(*) AS race_starts,
        SUM(r.points) AS total_points,
        -- is_win / is_podium are booleans pre-computed on the fact table
        -- (see 04-gold/04.Build Results Fact) - COUNT_IF just counts the
        -- TRUE rows, no position-range logic needs repeating here.
        COUNT_IF(r.is_win) AS number_of_wins,
        COUNT_IF(r.is_podium) AS number_of_podiums
    FROM formula1.gold.fact_session_results r
    JOIN formula1.gold.dim_constructors c
      ON r.constructor_id = c.constructor_id
  GROUP BY r.season,
        c.constructor_id,
        c.constructor_name,
        c.nationality)
SELECT season,
       constructor_id,
       constructor_name,
       nationality,
       -- Tie-break logic: rank by total points first, then by number of wins
       -- as the first tiebreaker - the same convention F1's own championship
       -- rules use. RANK() (rather than DENSE_RANK/ROW_NUMBER) means
       -- constructors tied on both points and wins share the same standing,
       -- and the next standing number is skipped accordingly (e.g. 1, 2, 2, 4).
       RANK() OVER (PARTITION BY season ORDER BY total_points DESC, number_of_wins DESC) AS standing,
       race_starts,
       total_points,
       number_of_wins,
       number_of_podiums
  FROM constructor_session_summary;


-- COMMAND ----------

SELECT * FROM formula1.gold.v_constructor_standing WHERE season = 2025