#import DAG
from airflow import DAG
# Pendulum is a Python date-and-time library that handles time zones cleanly. Airflow uses it for dates such as a DAG’s start_date.
from pendulum import datetime

@dag(schedule_interval='@daily', start_date=datetime(2023, 1, 1), catchup=False, tags=['healthcare'], description='healthcare data pipeline',doc_md=__doc__,)

#1. data generation task