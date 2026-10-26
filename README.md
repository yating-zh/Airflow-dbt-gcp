# End-to-End Data Pipeline Learning Project

This repository is a hands-on learning project following the tutorial **“End-to-End Data Pipeline with Airflow, dbt, Cosmos, GCS, BigQuery & more.”** It is intended to help me understand the tools and concepts used in data pipelines, including how they relate to data migration work.

> This is a learning project. The healthcare records generated here are synthetic and must not be treated as real patient data.

## What is in this repository?

- `dags/healthcare_dag.py` — Airflow DAG scaffold for the healthcare pipeline. The current file is not yet a complete, runnable end-to-end DAG.
- `include/raw_data_generation/healthcare_data.py` — generates random patient, electronic health record (EHR), and claims data, then uploads them to Google Cloud Storage (GCS).
- `include/gcp/` — local location for GCP credentials. The service-account key is secret and must not be committed.
- `requirements.txt` — Python dependencies for the project.
- `Dockerfile` — Astro Runtime image configuration.

## Current pipeline status

The data-generation script currently performs this flow:

```text
Faker and Python random functions
              ↓
Synthetic patient, EHR, and claims data
              ↓
GCS bucket: healthcare-data-2026-i
  ├── dev/
  └── prod/
```

For each environment, it writes:

- `patient_data.csv`
- `ehr_data.json` (newline-delimited JSON)
- `claims_data.parquet`

The script generates 5,000 records for `dev/` and 20,000 for `prod/`. The `prod/` name refers only to the larger tutorial dataset; it is not real production data.

**BigQuery loading, dbt transformations, and a complete Airflow orchestration are not currently implemented in this repository.** Those are part of the tutorial’s broader end-to-end goal and can be added as learning progresses.

## Prerequisites

- Python 3 and `venv` for running the generator locally
- A Google Cloud project with billing enabled and the Cloud Storage API enabled
- A GCS bucket you own
- A service account with permission to create/check the bucket and list, upload, and delete objects
- Docker and the Astro CLI if you want to run Airflow locally

GCP budgets send alerts; they are not hard spending caps. Review possible charges and set up billing alerts before using cloud services.

## Local setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pandas numpy Faker pyarrow
```

`google-cloud-storage` is listed in `requirements.txt`. The other packages are needed by the data-generation script when running it in a local virtual environment.

## Configure GCP credentials

1. Create or select your own Google Cloud project and create a service account for this project.
2. Grant it only the permissions it needs. This script creates/checks a bucket and lists, uploads, and deletes objects; a project-level `Storage Admin` role is a simple learning setup, but is broader than necessary.
3. Create and download a JSON key for that service account.
4. Place your key at:

   ```text
   include/gcp/service_account.json
   ```

   The script also checks `GOOGLE_APPLICATION_CREDENTIALS` and the standard Astro container path.

5. Keep the key private. `.gitignore` excludes files named `service_account.json`; never paste the key into source code, commit it, or share it in screenshots or chat.

The script is configured to use the bucket `healthcare-data-2026-i`. Create that bucket in your own GCP project, or change `BUCKET_NAME` in `include/raw_data_generation/healthcare_data.py` to your own bucket name.

## Run the data generator

From the repository root:

```bash
./.venv/bin/python include/raw_data_generation/healthcare_data.py
```

This command makes real changes in GCS. **Each run deletes all existing objects under the bucket’s `dev/` and `prod/` prefixes before generating and uploading new data.** Verify the bucket name and its contents before running; do not use it with data that must be retained.

## Run Airflow locally

With Docker and the Astro CLI installed:

```bash
astro dev start
```

This starts the local Astro/Airflow environment. The current DAG file is only a scaffold, so starting Airflow does not yet run a complete GCS-to-BigQuery-to-dbt pipeline.

## How this relates to a data migration project

The generator simulates test input; it does not extract records from a real source database. A typical migration or ELT flow might be:

```text
Source database
      ↓
Data acquisition / replication (for example, HVR)
      ↓
GCS files and/or BigQuery raw tables
      ↓
Airflow orchestration
      ↓
dbt transformations in BigQuery
      ↓
Analytics-ready models
```

The actual route depends on the company’s architecture. Raw data may land in GCS first, or be replicated directly into BigQuery. Airflow generally coordinates tasks, while dbt transforms data already available in the warehouse.

## Learning goals

- Understand Airflow DAGs, tasks, scheduling, and dependencies.
- Practice moving files through GCS and loading data into BigQuery.
- Learn how dbt models transform raw warehouse tables into analytics models.
- Understand how orchestration, data acquisition, storage, and transformation fit together.
