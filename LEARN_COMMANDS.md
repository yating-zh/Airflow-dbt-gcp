# Commands Used

Commands used while setting up the Astro project, installing dependencies, testing GCS access, running the data generator, and checking Git branches. Updated 2026-11-02.

## Astro and Docker setup

1. `docker --version` — confirmed Docker CLI version `29.8.2`.
2. `docker info` — checked Docker Engine; initially returned an HTTP 500 server error.
3. `astro version` — initially returned `command not found`; later reported Astro CLI version `1.46.1`.
4. `astro --version` — returned `command not found`.
5. `astro dev init` — initialized the Astro project.
6. `astro start` — failed because `start` is not a top-level Astro command.
7. `astro dev start` — attempted several times; earlier attempts failed because Docker was unavailable or could not access the iCloud Drive project directory. It later completed successfully.

## Python environment and GCS

Run these from the project root:

1. `python --version` — reported Python `3.10.8`.
2. `python3 -m venv .venv` — created a project virtual environment.
3. `source .venv/bin/activate` — activated the virtual environment.
4. `python -m pip install google-cloud-storage` — installed the GCS client library.
5. `python -m pip install -r requirements.txt` — installed dependencies listed in the requirements file.
6. `python -m pip install pandas numpy faker pyarrow` — installed the data-generation dependencies.
7. `python -c "from google.cloud import storage; print('ok')"` — verified the GCS library imports.
8. A credential test using `/usr/local/airflow/include/gcp/service_account.json` failed locally with `FileNotFoundError`; that is a container path, not the local Mac path.
9. A credential test using `include/gcp/service_account.json` printed `Connected`, confirming authentication.
10. `./.venv/bin/python include/raw_data_generation/healthcare_data.py` — generated synthetic data and uploaded CSV, newline-delimited JSON, and Parquet files to the GCS bucket. The script clears the `dev/` and `prod/` prefixes before uploading.

## Git branch checks

1. `git status --short --branch` — checked the current branch and working-tree changes.
2. `git branch --show-current` — confirmed the current branch.
3. `git remote -v` — checked the configured GitHub remote.
4. `git --no-pager log --oneline --decorate --graph --all -8` — inspected recent commits and branch positions after the PR merge.

## Notes

- In VS Code, `Python: Select Interpreter` is a Command Palette action, not a shell command.
- The data generator uses the service account JSON as a credential. Never commit or share that file.
- Airflow displayed a DAG import error because the installed Airflow version rejected `schedule_interval`; use `schedule` with the current `@dag` decorator.
