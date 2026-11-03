# Import DAG decorator and BashOperator
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
# Pendulum is a Python date-and-time library that handles time zones cleanly. Airflow uses it for dates such as a DAG’s start_date.
from pendulum import datetime
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.models import Variable
from pathlib import Path

PATH_TO_DATA_SCRIPT = '/usr/local/airflow/include/raw_data_generation/healthcare_data.py'
PATH_TO_SQL_SCRIPT = '/usr/local/airflow/include/raw_data_generation/create_external_tables.sql'
GCP_CONN_ID=Variable.get("GCP_CONN_ID", default_var="gcp_default")
#default_var="gcp_default"，这里是因为airflow设置的gcp connection id就是“gcp_default”

with open(PATH_TO_SQL_SCRIPT, 'r') as file:
    CREATE_EXTERNAL_TABLES_SQL = file.read()

@dag(schedule='@daily', 
     start_date=datetime(2026, 1, 1), 
     catchup=False, 
     tags=['healthcare'], 
     description='healthcare data pipeline',
     doc_md=__doc__,) #doc_md是DAG的文档说明，可以用来描述DAG的功能和用途。这里用__doc__表示使用当前文件的文档字符串作为DAG的文档说明。

#ddbt_healthcare_pipeline 是 dag function的名字，用来定义一个dag。dag function是一个Python函数，里面可以定义多个task。每个task都是一个operator，用来执行具体的操作。dag function的返回值是一个DAG对象，表示整个dag的结构和依赖关系。
def dbt_healthcare_pipeline():
    #Task1
    #generate_data_task 是 dag function中的一个task
    generate_data_task = BashOperator( #bashOperator是Airflow中用来执行bash命令的operator。这里用来执行生成raw data的脚本。
        task_id='generate_data', #task id在airflow的dashboard中显示的任务名称。这里用来标识生成raw data的任务。
        bash_command=f'python {PATH_TO_DATA_SCRIPT}',
    )
    #Task2
    create_external_tables_task = BigQueryInsertJobOperator( #BigQueryInsertJobOperator是Airflow中用来执行BigQuery SQL语句的operator。这里用来执行创建external table的SQL语句。
        task_id='create_external_tables', #task id在airflow的dashboard中显示的任务名称。这里用来标识创建external table的任务。
        configuration={
            "query": {
                "query": CREATE_EXTERNAL_TABLES_SQL, #SQL文件内容作为查询语句
                "useLegacySql": False, #使用标准SQL
            }
        },
        location='australia-southeast2', #这里和bigquery dataset一致
        gcp_conn_id=GCP_CONN_ID, #gcp_conn_id是Airflow中用来连接GCP的连接id。这里用来指定连接GCP的方式。
    )

    #call the task
    generate_data_task >> create_external_tables_task
dbt_healthcare_pipeline()
#常见的operator有：BashOperator, PythonOperator, EmailOperator, SlackOperator等。
# BashOperator是用来执行bash命令的，
# PythonOperator是用来执行Python函数的，
# EmailOperator是用来发送邮件的，
# SlackOperator是用来发送Slack消息的。
# 也可以自定义operator，比如自定义一个operator来执行dbt命令，或者自定义一个operator来执行Spark作业。