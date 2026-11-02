# copy and pasted from repo: https://github.com/ChuquEmeka/Airflow-dbt-bigquery-gcs-healthcare-data-pipeline/blob/main/include/raw_data_generation/healthcare_data.py
# Python script的作用是生成模拟医疗数据prod &。dev的raw data，并把它们上传到 Google Cloud Storage（GCS）
# =========================
# 1) Import required libraries
# =========================
import os
import pandas as pd
import numpy as np
from faker import Faker
# faker is a Python library that generates fake data such as names, addresses, and phone numbers. It is used here to create realistic-looking synthetic healthcare records for testing and development purposes.
import random
from datetime import datetime
import pyarrow as pa
import pyarrow.parquet as pq
import io
import json
from google.cloud import storage

# =========================
# 2) Connect to GCS
# =========================
# Service account credential path for Google Cloud Storage access.
# This file is expected to contain the GCP service account JSON key.
# We check a few common locations so the script works both in a local dev environment
# and inside the Airflow/Astro container, where the path is usually /usr/local/airflow/...
# keyfile_path = "C:/Users/User/Desktop/Projects/healthcare-data-project-442109-f33db94a36a9.json"
base_dir = os.path.dirname(os.path.abspath(__file__))
possible_paths = [
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    "/usr/local/airflow/include/gcp/service_account.json",
    os.path.abspath(os.path.join(base_dir, "..", "gcp", "service_account.json")),
    os.path.abspath(os.path.join(base_dir, "gcp", "service_account.json")),
]

keyfile_path = next((path for path in possible_paths if path and os.path.exists(path)), possible_paths[-1])
print(f"Using GCS credentials from: {keyfile_path}")
storage_client = storage.Client.from_service_account_json(keyfile_path)
# storage.Client.from_service_account_json()用来创建一个GCS object，使用指定的service account JSON key来进行身份验证。这个对象可以用来访问和操作GCS中的bucket和文件。

# Test the connection by listing accessible buckets in GCS.
buckets = list(storage_client.list_buckets())
print("Successfully connected to GCS. Available buckets:")
for bucket in buckets:
    print(f" - {bucket.name}")

# Faker instance used to generate realistic-looking synthetic healthcare records.
fake = Faker()

# =========================
# 3) Define bucket and storage paths
# =========================
# Bucket name where raw data will be stored.
BUCKET_NAME = 'healthcare-data-2026-i'
#cloud storage是一个云端存储服务，类似于一个在线硬盘，可以用来存放和管理数据。
#而bucket相当于一个文件夹，里面可以存放很多文件。这个bucket是用来存放raw data的。
#而blob相当于是bucket里面的一个文件，可以是文本、图片、视频等各种类型的数据。

# Prefix/folder names in the bucket for development and production data.
DEV_PATH = 'dev/'
PROD_PATH = 'prod/'
#healthcare-data-2026-i下dev和prod是两个文件夹，分别存放dev和prod环境的raw data。

# Number of synthetic records to generate for each environment.
DEV_RECORDS = 5000
PROD_RECORDS = 20000

# Date range for generated records.
start_date = datetime(2024, 11, 11)
end_date = datetime.today()


# =========================
# 4) Cloud Storage helper functions
# =========================
# Create the bucket if it does not already exist.
# create_bucket是自己写的函数，用来创建一个bucket，如果这个bucket已经存在，就不创建了。
def create_bucket():
    try:
        bucket = storage_client.bucket(BUCKET_NAME) #用storage_client.bucket()方法来获取一个bucket对象，参数是bucket的名字。
        if not bucket.exists():
            storage_client.create_bucket(BUCKET_NAME)
            print(f"Bucket '{BUCKET_NAME}' created successfully.")
        else:
            print(f"Bucket '{BUCKET_NAME}' already exists.")
    except Exception as e:
        print(f"Error creating bucket: {e}")


# Delete any existing files under a specific GCS folder prefix.
#每次生成新的raw data之前，先清空GCS中对应的文件夹，以避免旧数据干扰。
def empty_gcs_folder(path): 
    print(f"Emptying folder '{path}' in GCS bucket '{BUCKET_NAME}'...")
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs(prefix=path)
    for blob in blobs:
        blob.delete()
        print(f"Deleted '{blob.name}'")
    print(f"Completed emptying folder '{path}'.")


# =========================
# 5) Upload functions
# =========================
# Upload data in the chosen format to GCS.
def upload_to_gcs(data, path, filename, file_format):
    print(f"Uploading {filename} in {file_format} format to GCS...")
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(path + filename) 
    #blob是GCS中的一个对象，可以是文件或其他数据。这里用bucket.blob()方法来创建一个blob对象，参数是文件的路径和名字。
    #blob和bucket的关系就像文件和文件夹的关系，blob是bucket中的一个文件。
    #blob = Binary Large Object，意思是二进制大对象，可以用来存储各种类型的数据，包括文本、图片、音频、视频等。

    # Upload CSV data as text.
    if file_format == 'csv':
        csv_data = data.to_csv(index=False)
        blob.upload_from_string(csv_data, content_type='text/csv')

    # Upload JSONL data as newline-delimited JSON strings.
    elif file_format == 'json':
        json_data = "\n".join(data)
        blob.upload_from_string(json_data, content_type='application/json')

    # Upload Parquet data using PyArrow.
    #parquet是一种列式存储格式，适合大数据处理和分析。PyArrow是一个Python库，用来读写Parquet文件。
    elif file_format == 'parquet':
        buffer = io.BytesIO()
        pq.write_table(data, buffer)
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type='application/octet-stream')

    print(f"Uploaded {filename} to {path}")

# =========================
# 6) Data generation functions
# =========================
# Generate patient demographic records and return them as a pandas DataFrame.
def generate_patients(num_records):
    print("Generating patient demographic data in CSV format...")
    patients = []
    for _ in range(num_records):
        patient_id = fake.unique.uuid4()
        first_name = fake.first_name()
        last_name = fake.last_name()
        age = random.randint(0, 100)
        gender = random.choice(['Male', 'Female'])
        zip_code = fake.zipcode()
        insurance_type = random.choice(['Private', 'Medicare', 'Medicaid'])
        registration_date = fake.date_between(start_date=start_date, end_date=end_date)

        patients.append({
            'patient_id': patient_id,
            'first_name': first_name,
            'last_name': last_name,
            'age': age,
            'gender': gender,
            'zip_code': zip_code,
            'insurance_type': insurance_type,
            'registration_date': str(registration_date)
        })
    return pd.DataFrame(patients)


# Generate synthetic electronic health records (EHR).
# Each record is stored as a JSON string so it can be uploaded as newline-delimited JSON.
def generate_ehr(num_records, patient_ids):
    print("Generating electronic health records data in newline-delimited JSON format...")
    ehr_records = []
    for _ in range(num_records):
        patient_id = random.choice(patient_ids)
        visit_date = fake.date_between(start_date=start_date, end_date=end_date)
        diagnosis_code = random.choice(['E11.9', 'I10', 'J45', 'N18.9', 'Z00.0'])
        diagnosis_desc = {
            'E11.9': 'Type 2 diabetes mellitus',
            'I10': 'Essential hypertension',
            'J45': 'Asthma',
            'N18.9': 'Chronic kidney disease',
            'Z00.0': 'General medical exam'
        }[diagnosis_code]
        heart_rate = random.randint(60, 190)
        blood_pressure = f"{random.randint(110, 220)}/{random.randint(70, 90)}"
        temperature = round(random.uniform(97.0, 99.5), 1)

        ehr_record = {
            'patient_id': patient_id,
            'visit_date': str(visit_date),
            'diagnosis_code': diagnosis_code,
            'diagnosis_desc': diagnosis_desc,
            'heart_rate': heart_rate,
            'blood_pressure': blood_pressure,
            'temperature': temperature
        }

        ehr_records.append(json.dumps(ehr_record))

    return ehr_records


# Generate healthcare claims and explicitly define the Parquet schema
# so the output is consistent and ready for downstream data warehouse loads.
def generate_claims(num_records, patient_ids):
    print("Generating claims data in Parquet format with explicit schema...")
    claims = []
    for _ in range(num_records):
        claim_id = fake.unique.uuid4()
        patient_id = random.choice(patient_ids)
        provider_id = fake.unique.uuid4()
        service_date = fake.date_between(start_date=start_date, end_date=end_date)
        service_date = datetime.combine(service_date, datetime.min.time())
        diagnosis_code = random.choice(['E11.9', 'I10', 'J45', 'N18.9'])
        procedure_code = random.choice(['99213', '80053', '83036', '93000'])
        claim_amount = round(random.uniform(100, 15000), 3)
        status = random.choice(['Paid', 'Denied', 'Pending'])

        claims.append({
            'claim_id': str(claim_id),
            'patient_id': str(patient_id),
            'provider_id': str(provider_id),
            'service_date': service_date,
            'diagnosis_code': diagnosis_code,
            'procedure_code': procedure_code,
            'claim_amount': float(claim_amount),
            'status': status
        })

    # Define explicit schema for Parquet output.
    schema = pa.schema([
        ('claim_id', pa.string()),
        ('patient_id', pa.string()),
        ('provider_id', pa.string()),
        ('service_date', pa.timestamp('ms')),
        ('diagnosis_code', pa.string()),
        ('procedure_code', pa.string()),
        ('claim_amount', pa.float64()),
        ('status', pa.string())
    ])

    table = pa.Table.from_pandas(pd.DataFrame(claims), schema=schema)
    return table
#为什么这里有data frame，jason 还有parquet三种格式呢？因为不同的下游系统可能需要不同的数据格式。比如，CSV适合简单的数据分析，JSON适合web应用，Parquet适合大数据处理和分析。
#而且这里的三种format用来生成不同的raw data，分别是patient data，ehr data和claims data。因为不同的raw data有不同的结构和用途，所以需要不同的format来存储和传输。

# =========================
# 7) Main execution block
# =========================
# Create the GCS bucket and generate raw healthcare data for both dev and prod environments.
create_bucket()

# Generate DEV data.
empty_gcs_folder(DEV_PATH)
dev_patients = generate_patients(DEV_RECORDS)
dev_ehr = generate_ehr(DEV_RECORDS, dev_patients['patient_id'].tolist())
dev_claims = generate_claims(DEV_RECORDS, dev_patients['patient_id'].tolist())

upload_to_gcs(dev_patients, DEV_PATH, 'patient_data.csv', 'csv')
upload_to_gcs(dev_ehr, DEV_PATH, 'ehr_data.json', 'json')
upload_to_gcs(dev_claims, DEV_PATH, 'claims_data.parquet', 'parquet')

# Generate PROD data.
empty_gcs_folder(PROD_PATH)
prod_patients = generate_patients(PROD_RECORDS)
prod_ehr = generate_ehr(PROD_RECORDS, prod_patients['patient_id'].tolist())
prod_claims = generate_claims(PROD_RECORDS, prod_patients['patient_id'].tolist())

upload_to_gcs(prod_patients, PROD_PATH, 'patient_data.csv', 'csv')
upload_to_gcs(prod_ehr, PROD_PATH, 'ehr_data.json', 'json')
upload_to_gcs(prod_claims, PROD_PATH, 'claims_data.parquet', 'parquet')

print("Data generation and upload to GCS completed successfully.")