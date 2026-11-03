# Task 1: Generate Synthetic Healthcare Data and Upload It to GCS

This guide records how to reproduce the current task: generate synthetic healthcare data, upload it to your GCS bucket, and run the generator through a local Airflow DAG.

> The records are synthetic, generated with Faker and Python random functions. They do not come from a hospital, a real database, or real patients. The `prod/` prefix is only a larger tutorial sample, not production data.

## What this task does

```text
Airflow DAG
    ↓ runs a BashOperator task
healthcare_data.py
    ↓ generates random patient, EHR, and claims records
GCS bucket
    ├── dev/
    │   ├── patient_data.csv
    │   ├── ehr_data.json
    │   └── claims_data.parquet
    └── prod/
        ├── patient_data.csv
        ├── ehr_data.json
        └── claims_data.parquet
```

The current script generates 5,000 records for `dev/` and 20,000 for `prod/`. Every run deletes existing objects under both prefixes before uploading new files. Do not run it against data that must be retained.

This task stops at GCS. It does not load data into BigQuery or run dbt.

## Prerequisites

- A Google Cloud project with billing enabled and the Cloud Storage API enabled.
- A GCS bucket that you own. This project currently uses `healthcare-data-2026-i`.
- A service account with permission to list the required buckets, create/check the bucket, list objects, upload objects, and delete objects.
- Docker Desktop and the Astro CLI for local Airflow.
- Python 3 for running and testing the generator directly on your Mac.

GCP budget alerts are notifications, not a hard spending cap. Review potential charges and configure billing alerts.

## Step 1: Create a service account and prepare credentials

1. In Google Cloud Console, select your own project and enable the Cloud Storage API.
2. Create a dedicated service account, for example `airflow-gcs-sa`.
3. Grant it the required Storage permissions. `Storage Admin` at project level is a simple learning setup, but grants broader permissions than bucket-level access.
4. Create and download a JSON key for that service account.
5. In the repository, create this directory if needed:

   ```text
   include/gcp/
   ```

6. Put your downloaded key there and name it:

   ```text
   include/gcp/service_account.json
   ```

7. Keep this key secret. The repository `.gitignore` excludes `service_account.json`. Never commit it, paste its contents into source code, or share it in chat or screenshots.

The generator checks `GOOGLE_APPLICATION_CREDENTIALS`, the standard Astro container path, and paths relative to its own file to find the key.

## Step 2: Create the data-generation script

Create:

```text
include/raw_data_generation/healthcare_data.py
```

Use the tutorial's script from [the original repository](https://github.com/ChuquEmeka/Airflow-dbt-bigquery-gcs-healthcare-data-pipeline/blob/main/include/raw_data_generation/healthcare_data.py), including the local credential-path handling added for this project.

Check these settings near the top of the script:

- `BUCKET_NAME` must match a bucket you own; currently it is `healthcare-data-2026-i`.
- The service-account JSON must resolve to `include/gcp/service_account.json` locally and `/usr/local/airflow/include/gcp/service_account.json` in the Astro container.
- The script must use the GCS client created from your own service-account key.

The script generates patient demographics as CSV, EHR records as newline-delimited JSON, and claims as Parquet.

## Step 3: Set up a local Python environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pandas numpy Faker pyarrow
```

`requirements.txt` currently lists `google-cloud-storage`; the additional packages are needed by the generator when running it directly on your Mac.

Verify the GCS package imports:

```bash
./.venv/bin/python -c "from google.cloud import storage; print('GCS client import works')"
```

## Step 4: Test the generator directly

Run from the repository root:

```bash
./.venv/bin/python include/raw_data_generation/healthcare_data.py
```

Check the output for:

- The credentials path it selected.
- `Successfully connected to GCS`.
- Your bucket name in the list of accessible buckets.
- Successful uploads to both `dev/` and `prod/`.
- `Data generation and upload to GCS completed successfully.`

This command writes to GCS and deletes existing objects under `dev/` and `prod/` first.

## Step 5: Configure the Astro Runtime image

The current project Dockerfile uses Astro Runtime 12.7.1 and installs dbt and generator dependencies in the container:

```dockerfile
FROM quay.io/astronomer/astro-runtime:12.7.1
```

Its custom setup creates a container-side virtual environment and installs `dbt-bigquery==1.9.2`, pandas, Faker, PyArrow, and NumPy. These packages are separate from the Mac's `.venv`.

Build the image:

```bash
astro dev build
```

Wait for the build to complete successfully before starting Airflow.

## Step 6: Define the Airflow DAG

Create or update:

```text
dags/healthcare_dag.py
```

The current DAG:

- Imports `dag` and `BashOperator`.
- Uses `schedule='@daily'`, `catchup=False`.
- Defines a `generate_data` task that runs:
  `/usr/local/airflow/include/raw_data_generation/healthcare_data.py`
- Calls the DAG factory at module level so Airflow can discover the DAG.

The path must be `/usr/local/...` (`usr`, not `user`), because the task runs inside the Airflow container. A `BashOperator` is registered when it is created; a standalone line containing only the task variable does not execute it or define ordering.

## Step 7: Start local Airflow and run the task

Make sure Docker Desktop is running. Then, from the repository root:

```bash
docker info
astro dev start
```

Open the local Airflow UI at `http://localhost:8080` (or the URL shown by Astro CLI) and log in using the local credentials provided by your Astro/Airflow setup.

1. Find the `healthcare` DAG and confirm there is no import error.
2. Trigger the DAG manually for a learning run, or let its daily schedule trigger it.
3. Open the `generate_data` task logs and confirm the GCS upload succeeded.
4. Verify the three files exist under each of `dev/` and `prod/` in your bucket.

Before triggering, check the bucket and remember that this task clears its `dev/` and `prod/` prefixes each time.

## Troubleshooting

### `ImportError: cannot import name 'storage' from 'google.cloud'`

The active Python environment is missing the GCS library. Install it into the same environment used to run the command:

```bash
./.venv/bin/python -m pip install google-cloud-storage
```

### `ModuleNotFoundError` for pandas, Faker, PyArrow, or NumPy

Install the generator dependencies into the local `.venv`:

```bash
./.venv/bin/python -m pip install pandas numpy Faker pyarrow
```

### `FileNotFoundError` for `/usr/local/airflow/.../service_account.json`

That is the container path and may not exist on your Mac. Confirm the local key is at `include/gcp/service_account.json`. The script should resolve the local path relative to `healthcare_data.py`.

### GCS `403 Forbidden`, such as `storage.buckets.get` or `storage.objects.list`

Authentication worked, but the service account is not authorized for the bucket or project. Confirm:

- `BUCKET_NAME` is your own bucket, not the tutorial author's bucket.
- The service account from your JSON key has the necessary Storage roles on your project or bucket.
- IAM changes have had time to propagate.

### Docker returns `500 Internal Server Error`

Docker CLI is running but Docker Engine is not responding. Restart Docker Desktop, wait until its engine is running, verify `docker info` shows Server details, then check:

```bash
astro dev ps
```

If no containers are listed, retry `astro dev start`.

### Image build fails while compiling `cffi` with `No such file or directory: 'cc'`

This happened with Astro Runtime 3.3-11 (Python 3.14) and the older `dbt-bigquery==1.5.3`, whose dependency set attempted to compile `cffi` without a compiler. The working combination used for this project is Astro Runtime 12.7.1 (Python 3.12) with `dbt-bigquery==1.9.2`. Keep the Runtime and dbt versions aligned rather than adding a compiler as the first workaround.

### Airflow says the metadata database needs an upgrade or shows an `execution_date` error

This can happen after changing Astro Runtime/Airflow versions while keeping the old local Postgres metadata database. If you do not need local Airflow history, connections, variables, or task logs, `astro dev kill` resets the local environment and deletes that data. Do not run it if you need to keep those records.

### DAG import error: unexpected keyword `schedule_interval`

Use `schedule='@daily'` with the current `@dag` decorator.

### Task cannot find `healthcare_data.py`

Check that the DAG command uses the container path:

```text
/usr/local/airflow/include/raw_data_generation/healthcare_data.py
```

The task runs inside the container, not directly from the Mac's project path.

### See Airflow logs

```bash
astro dev logs --webserver
astro dev logs --scheduler
```

## Current scope and next learning step

This task generates synthetic raw files and puts them in GCS. The current DAG does not load them into BigQuery or run dbt yet. A later task can add GCS-to-BigQuery loading, raw tables, and dbt transformations.
