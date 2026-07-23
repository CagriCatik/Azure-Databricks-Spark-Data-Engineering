# Raw Data ERD — Step-by-Step Explanation

## 1. Purpose of the raw data model

The raw data model represents the Formula 1 datasets as they are received from the source system.

It contains six entities:

```text
circuits
races
constructors
drivers
results
sprints
```

The model is source-oriented. Therefore, it preserves:

* original column names such as `circuitId` and `raceName`;
* original URLs;
* repeated race information inside result datasets;
* separate tables for race results and sprint results;
* the original relationships between the source entities.

At this stage, the objective is not to create an optimized analytical model. The objective is to store the source data accurately and preserve its original structure.

---

# 2. Understanding the ERD notation

The diagram uses the following abbreviations:

| Abbreviation        | Meaning                                                  |
| ------------------- | -------------------------------------------------------- |
| `PK`                | Primary key                                              |
| `FK1`, `FK2`, `FK3` | Foreign-key relationship                                 |
| `PK, FK1`           | Column is part of the primary key and also a foreign key |
| Underlined column   | Key column                                               |

A primary key uniquely identifies a record.

A foreign key connects a record to another entity.

For example:

```text
races.circuitId → circuits.circuitId
```

This means that every race references a circuit.

---

# 3. Entity overview

The model can be divided into three logical areas.

## 3.1 Reference entities

These entities describe relatively stable objects:

```text
circuits
constructors
drivers
```

## 3.2 Event entity

The `races` entity describes a race event in a specific season and round.

```text
races
```

## 3.3 Result entities

These entities contain the performance of drivers and constructors during race sessions:

```text
results
sprints
```

---

# 4. Step 1: `circuits` entity

## 4.1 Purpose

The `circuits` table stores information about Formula 1 racing circuits.

Examples include:

* Silverstone Circuit;
* Monza;
* Monaco;
* Spa-Francorchamps;
* Suzuka.

## 4.2 Grain

One row represents one circuit.

The grain can be expressed as:

> One record per Formula 1 circuit.

## 4.3 Primary key

```text
circuitId
```

`circuitId` uniquely identifies a circuit.

Example:

| circuitId | circuitName                    |
| --------: | ------------------------------ |
|         1 | Albert Park Grand Prix Circuit |
|         9 | Silverstone Circuit            |
|        14 | Autodromo Nazionale di Monza   |

## 4.4 Columns

| Column        | Description                                          |
| ------------- | ---------------------------------------------------- |
| `circuitId`   | Unique circuit identifier                            |
| `url`         | Source URL containing additional circuit information |
| `circuitName` | Name of the circuit                                  |
| `lat`         | Latitude                                             |
| `lng`         | Longitude                                            |
| `locality`    | City or local area                                   |
| `country`     | Country in which the circuit is located              |

The image may visually resemble `Ing`, but the intended field is normally `lng`, meaning longitude.

## 4.5 Relationship

The circuit is referenced by the `races` table:

```text
circuits.circuitId
        ↓
races.circuitId
```

The relationship is:

```text
One circuit → many races
```

A circuit may host races across several seasons.

For example, Silverstone may appear in:

```text
2023 round 10
2024 round 12
2025 round 11
```

All these race records can reference the same `circuitId`.

---

# 5. Step 2: `races` entity

## 5.1 Purpose

The `races` table stores information about race events.

A race is identified by its season and its round within that season.

Examples:

```text
2025 season, round 1
2025 season, round 2
2026 season, round 1
```

## 5.2 Grain

One row represents one Formula 1 race weekend or race event in a specific season and round.

The grain is:

> One record per season and round.

## 5.3 Composite primary key

The primary key consists of two columns:

```text
season
round
```

Neither column is sufficient by itself.

### Why `season` alone is insufficient

A season contains multiple rounds.

```text
2025 round 1
2025 round 2
2025 round 3
```

### Why `round` alone is insufficient

Round numbers are repeated every season.

```text
2024 round 1
2025 round 1
2026 round 1
```

Therefore, the unique race identifier is:

```text
season + round
```

Example:

| season | round | raceName              |
| -----: | ----: | --------------------- |
|   2025 |     1 | Australian Grand Prix |
|   2025 |     2 | Chinese Grand Prix    |
|   2026 |     1 | Australian Grand Prix |

## 5.4 Columns

| Column      | Description                           |
| ----------- | ------------------------------------- |
| `season`    | Formula 1 championship season         |
| `round`     | Round number within the season        |
| `url`       | Source URL for the race               |
| `raceName`  | Name of the race                      |
| `date`      | Race date                             |
| `circuitId` | Circuit at which the race takes place |

## 5.5 Foreign key

```text
circuitId
```

The relationship is:

```text
races.circuitId → circuits.circuitId
```

This means that every race must refer to a circuit.

## 5.6 Relationships to result tables

The composite race key is referenced by both result entities:

```text
races.season → results.season
races.round  → results.round
```

and:

```text
races.season → sprints.season
races.round  → sprints.round
```

The relationships are:

```text
One race → many race results
One race → many sprint results
```

A single race weekend can contain results for many drivers.

---

# 6. Step 3: `constructors` entity

## 6.1 Purpose

The `constructors` table stores Formula 1 teams or constructors.

Examples include:

* Ferrari;
* Mercedes;
* McLaren;
* Red Bull Racing;
* Aston Martin.

## 6.2 Grain

One row represents one constructor.

The grain is:

> One record per Formula 1 constructor.

## 6.3 Primary key

```text
constructorId
```

This uniquely identifies the constructor.

Example:

| constructorId | name     |
| ------------- | -------- |
| 1             | McLaren  |
| 6             | Ferrari  |
| 9             | Red Bull |

## 6.4 Columns

| Column          | Description                                        |
| --------------- | -------------------------------------------------- |
| `constructorId` | Unique constructor identifier                      |
| `name`          | Constructor or team name                           |
| `nationality`   | Nationality associated with the constructor        |
| `url`           | Source URL with additional constructor information |

## 6.5 Relationships

The constructor is referenced by both `results` and `sprints`.

```text
constructors.constructorId
        ↓
results.constructorId
```

```text
constructors.constructorId
        ↓
sprints.constructorId
```

The relationships are:

```text
One constructor → many race results
One constructor → many sprint results
```

A constructor can participate in many rounds, seasons, and session types.

---

# 7. Step 4: `drivers` entity

## 7.1 Purpose

The `drivers` table stores information about Formula 1 drivers.

## 7.2 Grain

One row represents one driver.

The grain is:

> One record per Formula 1 driver.

## 7.3 Primary key

```text
driverId
```

This uniquely identifies the driver.

Example:

| driverId | name           |
| -------- | -------------- |
| 1        | Lewis Hamilton |
| 4        | Lando Norris   |
| 830      | Max Verstappen |

## 7.4 Columns

| Column        | Description                                         |
| ------------- | --------------------------------------------------- |
| `driverId`    | Unique driver identifier                            |
| `name`        | Driver name                                         |
| `dateOfBirth` | Driver date of birth                                |
| `nationality` | Driver nationality                                  |
| `url`         | Source URL containing additional driver information |

## 7.5 Relationships

The driver is referenced by both result tables:

```text
drivers.driverId
        ↓
results.driverId
```

```text
drivers.driverId
        ↓
sprints.driverId
```

The relationships are:

```text
One driver → many race results
One driver → many sprint results
```

A driver can participate in multiple rounds and seasons.

---

# 8. Step 5: `results` entity

## 8.1 Purpose

The `results` table stores the final results of the main race session.

It connects:

* a race;
* a driver;
* a constructor;
* the driver’s performance in that race.

## 8.2 Grain

One row represents:

> The race result of one driver, for one constructor, in one season and round.

An example record may mean:

> Driver 44 drove for constructor 131 in round 5 of the 2025 season.

## 8.3 Composite primary key

The primary key consists of four columns:

```text
season
round
constructorId
driverId
```

All four columns together identify one result record.

The key can be understood as:

```text
Race + constructor + driver
```

Example:

| season | round | constructorId | driverId |
| -----: | ----: | ------------: | -------: |
|   2025 |     1 |             1 |        4 |
|   2025 |     1 |             6 |       16 |
|   2025 |     1 |             9 |      830 |

## 8.4 Key columns and relationships

### Race key

```text
season
round
```

These columns reference the `races` table:

```text
results.season → races.season
results.round  → races.round
```

### Constructor key

```text
constructorId
```

This references:

```text
results.constructorId
    →
constructors.constructorId
```

### Driver key

```text
driverId
```

This references:

```text
results.driverId
    →
drivers.driverId
```

## 8.5 Columns

| Column          | Description                                  |
| --------------- | -------------------------------------------- |
| `season`        | Season of the race                           |
| `round`         | Round within the season                      |
| `constructorId` | Constructor used by the driver               |
| `driverId`      | Driver who produced the result               |
| `date`          | Race date                                    |
| `raceName`      | Race name                                    |
| `url`           | Source URL                                   |
| `grid`          | Starting grid position                       |
| `laps`          | Number of completed laps                     |
| `number`        | Car number                                   |
| `points`        | Points awarded                               |
| `position`      | Numeric final position                       |
| `positionText`  | Textual representation of the final position |
| `status`        | Completion or retirement status              |

## 8.6 Example

| Column          | Example             |
| --------------- | ------------------- |
| `season`        | 2025                |
| `round`         | 3                   |
| `constructorId` | 6                   |
| `driverId`      | 16                  |
| `raceName`      | Japanese Grand Prix |
| `grid`          | 4                   |
| `laps`          | 53                  |
| `number`        | 16                  |
| `points`        | 15                  |
| `position`      | 3                   |
| `positionText`  | `3`                 |
| `status`        | Finished            |

This record describes one driver’s result in the main race.

---

# 9. Step 6: `sprints` entity

## 9.1 Purpose

The `sprints` table stores the result of the sprint session.

A sprint is different from the main race, but its structure is similar.

It contains:

* race information;
* driver information;
* constructor information;
* sprint starting position;
* sprint finishing position;
* sprint points.

## 9.2 Grain

One row represents:

> The sprint result of one driver, for one constructor, in one season and round.

## 9.3 Composite primary key

The primary key is:

```text
season
round
constructorId
driverId
```

This is the same key structure as the `results` table.

The records remain unique because race results and sprint results are stored in separate tables.

## 9.4 Foreign keys

### Race relationship

```text
sprints.season → races.season
sprints.round  → races.round
```

### Constructor relationship

```text
sprints.constructorId
    →
constructors.constructorId
```

### Driver relationship

```text
sprints.driverId
    →
drivers.driverId
```

## 9.5 Columns

| Column          | Description                        |
| --------------- | ---------------------------------- |
| `season`        | Season containing the sprint       |
| `round`         | Round containing the sprint        |
| `constructorId` | Driver’s constructor               |
| `driverId`      | Driver participating in the sprint |
| `date`          | Session or race-weekend date       |
| `raceName`      | Race weekend name                  |
| `url`           | Source URL                         |
| `grid`          | Sprint starting position           |
| `laps`          | Completed sprint laps              |
| `number`        | Car number                         |
| `points`        | Sprint points                      |
| `position`      | Numeric finishing position         |
| `positionText`  | Textual finishing position         |
| `status`        | Sprint completion status           |

---

# 10. Step-by-step relationship flow

## 10.1 Circuit to race

The first relationship is:

```text
circuits
   │
   └── circuitId
          ↓
      races.circuitId
```

Interpretation:

> A race takes place at one circuit, while a circuit may host many races.

Cardinality:

```text
circuits 1 ─── N races
```

---

## 10.2 Race to race results

The next relationship is:

```text
races
  ├── season
  └── round
       ↓
results
  ├── season
  └── round
```

Interpretation:

> One race can have many driver results.

Cardinality:

```text
races 1 ─── N results
```

---

## 10.3 Race to sprint results

The same race may also have a sprint session:

```text
races
  ├── season
  └── round
       ↓
sprints
  ├── season
  └── round
```

Cardinality:

```text
races 1 ─── N sprints
```

Not every race weekend necessarily contains sprint data.

Therefore, from a business perspective, the relationship can be interpreted as:

```text
One race → zero or many sprint-result records
```

---

## 10.4 Constructor to results

```text
constructors.constructorId
        ↓
results.constructorId
```

Interpretation:

> One constructor can produce many race-result records.

```text
constructors 1 ─── N results
```

---

## 10.5 Constructor to sprints

```text
constructors.constructorId
        ↓
sprints.constructorId
```

Interpretation:

> One constructor can produce many sprint-result records.

```text
constructors 1 ─── N sprints
```

---

## 10.6 Driver to results

```text
drivers.driverId
       ↓
results.driverId
```

Interpretation:

> One driver can have many race results across different rounds and seasons.

```text
drivers 1 ─── N results
```

---

## 10.7 Driver to sprints

```text
drivers.driverId
       ↓
sprints.driverId
```

Interpretation:

> One driver can have many sprint results.

```text
drivers 1 ─── N sprints
```

---

# 11. Complete logical relationship map

```text
circuits
    │
    │ circuitId
    ▼
races
    │
    │ season + round
    ├───────────────────────┐
    ▼                       ▼
results                  sprints
    ▲                       ▲
    │                       │
    ├──── constructors ─────┤
    │                       │
    └──────── drivers ──────┘
```

More explicitly:

```text
circuits.circuitId
    → races.circuitId

races.(season, round)
    → results.(season, round)

races.(season, round)
    → sprints.(season, round)

constructors.constructorId
    → results.constructorId

constructors.constructorId
    → sprints.constructorId

drivers.driverId
    → results.driverId

drivers.driverId
    → sprints.driverId
```

---

# 12. End-to-end example

Assume the following source entities exist.

## Circuit

```text
circuitId  = 14
circuitName = Monza
country     = Italy
```

## Race

```text
season    = 2025
round     = 16
raceName  = Italian Grand Prix
circuitId = 14
```

The race references the circuit:

```text
races.circuitId = circuits.circuitId
```

## Constructor

```text
constructorId = 6
name          = Ferrari
```

## Driver

```text
driverId = 16
name     = Charles Leclerc
```

## Result

```text
season        = 2025
round         = 16
constructorId = 6
driverId      = 16
grid          = 2
laps          = 53
points        = 25
position      = 1
status        = Finished
```

This result record can be interpreted through its relationships:

```text
season + round
    → Italian Grand Prix

constructorId
    → Ferrari

driverId
    → Charles Leclerc

circuitId through races
    → Monza
```

The full business statement is:

> Charles Leclerc drove for Ferrari in the 2025 Italian Grand Prix at Monza and finished first.

---

# 13. Data-integrity rules

The ERD implies several important rules.

## 13.1 Circuit references must be valid

Every `races.circuitId` should exist in `circuits`.

Invalid example:

```text
races.circuitId = 999
```

when no circuit with ID `999` exists.

---

## 13.2 Race references must be valid

Every combination of `season` and `round` in `results` or `sprints` should exist in `races`.

Invalid example:

```text
results:
season = 2025
round  = 30
```

when season 2025 has no round 30 in the `races` table.

---

## 13.3 Constructor references must be valid

Every `constructorId` in `results` and `sprints` should exist in `constructors`.

---

## 13.4 Driver references must be valid

Every `driverId` in `results` and `sprints` should exist in `drivers`.

---

## 13.5 Result records must be unique

The following combination should occur only once in `results`:

```text
season
round
constructorId
driverId
```

The same rule applies separately to `sprints`.

---

# 14. Why some information is duplicated

The `results` and `sprints` tables contain:

```text
date
raceName
url
```

However, similar information already exists in `races`.

This creates source-level duplication.

For example:

```text
races.raceName
results.raceName
sprints.raceName
```

In a normalized relational model, the result tables would normally reference the race and would not repeat all race attributes.

However, this is a raw source model. Keeping these fields is reasonable because it:

* preserves the original source payload;
* avoids changing the source structure during ingestion;
* supports source validation;
* makes it possible to compare repeated source values;
* provides evidence of exactly what was delivered.

The duplicate fields can be removed or standardized later in the Silver layer.

---

# 15. Why `results` and `sprints` are separate

Both entities have nearly identical structures, but they represent different session types.

```text
results = main race results
sprints = sprint-session results
```

Keeping them separate in the raw layer has several benefits:

* the original source datasets remain unchanged;
* race and sprint records cannot be confused;
* ingestion logic can process each source independently;
* source-specific errors are easier to identify;
* no additional `sessionType` field must be introduced during raw ingestion.

They may later be combined in the Gold layer by adding a field such as:

```text
session_type = RACE
session_type = SPRINT
```

---

# 16. Raw data model summary

| Entity         | Grain                                | Primary key                                    | Main relationship                          |
| -------------- | ------------------------------------ | ---------------------------------------------- | ------------------------------------------ |
| `circuits`     | One circuit                          | `circuitId`                                    | Referenced by `races`                      |
| `races`        | One season and round                 | `season`, `round`                              | References `circuits`                      |
| `constructors` | One constructor                      | `constructorId`                                | Referenced by `results` and `sprints`      |
| `drivers`      | One driver                           | `driverId`                                     | Referenced by `results` and `sprints`      |
| `results`      | One driver-constructor race result   | `season`, `round`, `constructorId`, `driverId` | References races, constructors and drivers |
| `sprints`      | One driver-constructor sprint result | `season`, `round`, `constructorId`, `driverId` | References races, constructors and drivers |

The raw ERD establishes the source-level structure of the Formula 1 platform. `circuits`, `constructors`, and `drivers` provide descriptive entities; `races` identifies the event; and `results` and `sprints` store the measurable session outcomes.
