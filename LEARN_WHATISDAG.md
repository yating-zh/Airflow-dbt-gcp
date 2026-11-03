# What Is a DAG?

- **DAG** describes a set of logically related tasks, including when they run and in what order.
- **Schedule** determines when a DAG run starts.
- **Dependencies between tasks** determine what must finish before another task can run during that DAG run.

## Example 1: Independent Finance and Customer reports

You can create two DAGs and schedule both to run every day at 8:00 AM:

```text
finance_report_dag   → generate the Finance report
customer_report_dag  → generate the Customer report
```

They can be scheduled, monitored, and managed separately. However, they are not guaranteed to run at exactly the same time: Airflow concurrency limits or competition for shared resources may affect when they start.

## Example 2: An ordered data pipeline

Generating a CSV, uploading it to GCS, and loading it into BigQuery are usually tasks in the same DAG, with dependencies defining their order:

```text
generate_csv_task → upload_to_gcs_task → load_to_bigquery_task
```

Each task waits for the previous task to succeed. Together, the three tasks form a DAG run that starts according to the DAG's schedule, such as every day at 8:00 AM.

## Tasks can also run in parallel

Not every task needs its own DAG to run at the same time. Tasks in the same DAG can run in parallel when there is no dependency between them. Separate DAGs are often useful when workflows have different business purposes, schedules, owners, or monitoring needs.
