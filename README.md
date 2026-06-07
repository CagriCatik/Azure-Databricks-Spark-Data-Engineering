<h1 align="center">Azure Databricks for Data Engineers</h1>

<p align="center">
  <a href="https://mccatik.github.io/Azure-Databricks-Spark-Data-Engineering/">
    <img src="https://img.shields.io/badge/docs-GitHub%20Pages-222?logo=github" alt="GitHub Pages">
  </a>
  <a href="https://www.python.org">
    <img src="https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://azure.microsoft.com/products/databricks">
    <img src="https://img.shields.io/badge/platform-Azure%20Databricks-FF3621?logo=databricks&logoColor=white" alt="Platform: Azure Databricks">
  </a>
</p>

---

## Overview

This repository contains comprehensive documentation for building a cloud‑based
**Data Lakehouse** on Azure Databricks, following the **Medallion Architecture**
(Landing → Bronze → Silver → Gold). It uses a hands‑on **Formula 1** project to cover
Apache Spark (PySpark & Spark SQL), Delta Lake, Unity Catalog, Lakeflow Jobs, and
Databricks Dashboards & Genie.

## Documentation sections

|   | Section | Topics |
| --- | --- | --- |
| 01 | [Introduction](docs/01_introduction/) | Course overview & learning path |
| 02 | [Azure Subscription](docs/02_subscription/) | Free account, Azure portal |
| 03 | [Azure Databricks](docs/03_databricks/) | Intro, workspace, architecture |
| 04 | [Databricks Compute](docs/04_databricks-compute/) | Clusters, config, troubleshooting |
| 05 | [Databricks Notebooks](docs/05_databricks-notebook/) | Magic commands, `dbutils`, debugging |
| 06 | [Unity Catalog](docs/06_unity-catalog/) | Object model, metastore, cloud storage |
| 07 | [Formula 1 Project](docs/07_project-overview/) | Data, requirements, lakehouse, medallion |
| 08 | [Project Setup](docs/08_project-setup/) | Data lake & Unity Catalog environment |
| 09 | [Delta Lake](docs/09_delta-lake/) | Transaction log, time travel, ACID |
| 10 | [Data Ingestion — Bronze](docs/10_data-ingestion-bronze/) | DataFrameReader/Writer, schemas, JSON |
| 11 | [Data Transformation — Silver](docs/11_data-transformation-silver/) | Cleaning, dedupe, Lakeflow Jobs |
| 12 | [Data Transformation — Gold](docs/12_data-transformation-gold/) | Dimensional model, triggers, notifications |
| 13 | [Data Analytics](docs/13_data-analytics/) | Databricks SQL, dashboards, Genie |
| 14 | [Incremental Data Processing](docs/14_incremental-data-processing/) | *Coming soon* |

## Getting started


### Local setup

```bash
# 1. Clone the repository
git clone https://github.com/CagriCatik/Azure-Databricks-Spark-Data-Engineering.git
cd Azure-Databricks-Spark-Data-Engineering

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Preview & build

```bash
zensical serve          # live preview at http://localhost:8000
zensical build --clean  # build the static site into ./site
```
