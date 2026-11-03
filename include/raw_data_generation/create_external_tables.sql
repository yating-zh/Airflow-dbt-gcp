-- Creating patient_data external table (CSV format)
CREATE OR REPLACE EXTERNAL TABLE `healthcare-demo-2026.dev_healthcare_data.patient_data_external`
--format here: `GCP project_id.dataset_id.table_id`
--need to go to Bigquery and create a dataset "dev_healthcare_data".
OPTIONS (
  format = 'CSV',
  uris = ['gs://healthcare-data-2026-i/dev/patient_data.csv'],
    --Cloud Storage URI, copied from the GCS file info page
  skip_leading_rows = 1
);

-- Creating ehr_data external table (JSON format)
CREATE OR REPLACE EXTERNAL TABLE `healthcare-demo-2026.dev_healthcare_data.ehr_data_external`
OPTIONS (
  format = 'NEWLINE_DELIMITED_JSON',
  uris = ['gs://healthcare-data-2026-i/dev/ehr_data.json']
);

-- Creating claims_data external table (Parquet format with explicit schema)
CREATE OR REPLACE EXTERNAL TABLE `healthcare-demo-2026.dev_healthcare_data.claims_data_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://healthcare-data-2026-i/dev/claims_data.parquet']
);