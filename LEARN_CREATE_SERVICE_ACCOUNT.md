# Create a GCP Service Account for This Project

This note summarizes the setup needed for the script in `include/raw_data_generation/healthcare_data.py`.

## 1) Why you should not reuse someone else’s JSON key

Do not copy a service-account JSON from a tutorial or another repo.

That key is tied to:

- another Google Cloud project
- another set of permissions
- another bucket or dataset
- another account owner

Using it can cause:

- permission errors
- wrong project access
- security risk
- accidental access to someone else’s data

Use your own GCP project and your own service account.

## 2) Create your own Google Cloud project

1. Go to: https://console.cloud.google.com/
2. Select or create a project
3. Give it a clear name, for example:
   - `healthcare-demo-2026`
4. Note the project ID

## 3) Enable the required APIs

For this project, enable at least:

- Cloud Storage API

If you also want BigQuery later, enable:

- BigQuery API

Steps:

1. Open `APIs & Services` → `Library`
2. Search for `Cloud Storage API`
3. Click `Enable`

## 4) Create a service account

1. Go to: `IAM & Admin` → `Service Accounts`
2. Click `Create Service Account`
3. Name it something like:
   - `airflow-gcs-sa`
4. Click `Create and Continue`
5. Add the necessary roles
6. Click `Done`

## 5) Grant permissions

For this script, the service account must be able to:

- list buckets
- create buckets
- list objects in buckets
- upload files to GCS
- delete files in GCS

The easiest role is:

- `Storage Admin`

Alternative:

- `Storage Object Admin`
- `Storage Bucket Admin`

If you later add BigQuery, also add:

- `BigQuery Admin` (or relevant narrower BigQuery roles)

## 6) Create a JSON key

1. Open the service account
2. Go to `Keys`
3. Click `Add Key` → `Create new key`
4. Choose `JSON`
5. Download the file

Example filename:

- `my-project-12345-abcdef.json`

Important:

- Keep it secret
- Never commit it to Git
- Never share it in screenshots or chat
- Never upload it to public repos

## 7) Put the JSON in the correct project path

This script expects the credential at:

- `/usr/local/airflow/include/gcp/service_account.json`

In the repo, use a local path equivalent:

- `include/gcp/service_account.json`

The project structure should look like:

- `include/gcp/service_account.json`

This is the same file the script resolves when running locally.

## 8) Add it to `.gitignore`

The repo already includes a rule similar to:

```gitignore
**/service_account.json
```

This is important so the key is not committed.

## 9) Fix the script path issue

The original tutorial code used a container-only path:

```python
/usr/local/airflow/include/gcp/service_account.json
```

That path works only inside the Airflow/Astro container.

For local Mac development, use a path that resolves relative to the project, for example:

```python
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
keyfile_path = os.path.abspath(os.path.join(base_dir, "..", "gcp", "service_account.json"))
```

This makes the script work both locally and in the container.

## 10) Check the Python environment

Use a project virtual environment, not the system Python if you can avoid it.

Example:

```bash
cd /path/to/project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install the needed libraries:

```bash
python -m pip install google-cloud-storage pandas numpy faker pyarrow
```

## 11) Validate the credentials manually

Test the JSON file and GCS auth:

```bash
python -c "from google.cloud import storage; c = storage.Client.from_service_account_json('/path/to/project/include/gcp/service_account.json'); print('Connected')"
```

If that works, the key is valid and the service account is authenticated.

## 12) Run the script

From the project root:

```bash
./.venv/bin/python include/raw_data_generation/healthcare_data.py
```

That script will:

- create or check a GCS bucket
- empty `dev/` and `prod/` folders
- generate fake healthcare data
- upload CSV, JSON, and Parquet files to GCS

## 13) Why the script failed before

The most common reasons were:

- the JSON file was missing
- the path was wrong
- the service account had no GCS permissions
- the bucket name was invalid or inaccessible
- the script was trying to access a bucket without `storage.buckets.get` and `storage.objects.list` permissions

The key error was:

```text
403 Forbidden
storage.buckets.get access denied
storage.objects.list access denied
```

This means:

- the credentials are recognized
- but the service account is not authorized to use that bucket

## 14) Fix the permissions

In the GCP Console:

1. Go to `IAM & Admin` → `IAM`
2. Find your service account
3. Add the role `Storage Admin` (simplest)
4. Wait a moment for IAM propagation
5. Re-run the script

## 15) Best practice

For a learning project:

- create a dedicated project
- create a dedicated service account
- provide only the necessary roles
- keep the JSON outside Git
- protect the key as a secret
- use environment variables or relative paths when possible

## 16) Final takeaway

To use this repo safely:

1. create your own GCP project
2. create your own service account
3. generate your own JSON key
4. grant Storage permissions
5. place the file in `include/gcp/service_account.json`
6. keep it out of Git
7. run the script in a local venv or Astro/Airflow environment

This is the correct setup pattern for this project.
