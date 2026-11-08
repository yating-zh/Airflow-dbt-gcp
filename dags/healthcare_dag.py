# Import DAG decorator and BashOperator
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
# Pendulum is a Python date-and-time library that handles time zones cleanly. Airflow uses it for dates such as a DAG’s start_date.
from pendulum import datetime
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.models import Variable
from pathlib import Path
from cosmos import DbtTaskGroup
from include.dbt.healthcare_dbt_bigquery_data_pipeline.cosmos_config import DBT_CONFIG, DBT_PROJECT_CONFIG
from cosmos.constants import LoadMode
from cosmos.config import RenderConfig


PATH_TO_DATA_SCRIPT = '/usr/local/airflow/include/raw_data_generation/healthcare_data.py'
PATH_TO_SQL_SCRIPT = '/usr/local/airflow/include/raw_data_generation/create_external_tables.sql'
GCP_CONN_ID=Variable.get("GCP_CONN_ID", default_var="gcp_default")
#default_var="gcp_default"，这里是因为airflow设置的gcp connection id就是“gcp_default”
TARGET_ENV=DBT_CONFIG.target_name

with open(PATH_TO_SQL_SCRIPT, 'r') as file:
    CREATE_EXTERNAL_TABLES_SQL = file.read()\
    .replace("dev_healthcare_data",f"{TARGET_ENV}_healthcare_data")\
    .replace("/dev/", f"/{TARGET_ENV}/")

@dag(schedule='@daily', 
     start_date=datetime(2026, 1, 1), 
     catchup=False, 
     tags=['healthcare'], 
     description='healthcare data pipeline',
     doc_md=__doc__,) #doc_md是DAG的文档说明，可以用来描述DAG的功能和用途。这里用__doc__表示使用当前文件的文档字符串作为DAG的文档说明。

#ddbt_healthcare_pipeline 是 dag function的名字，用来定义一个dag。dag function是一个Python函数，里面可以定义多个task。每个task都是一个operator，用来执行具体的操作。dag function的返回值是一个DAG对象，表示整个dag的结构和依赖关系。
def dbt_healthcare_pipeline():
    #Task1
    #task1 任务是生成raw data到gcs bucket中，raw data格式有jason，csv，parquet三种
    #generate_data_task 是 dag function中的一个task
    generate_data_task = BashOperator( #bashOperator是Airflow中用来执行bash命令的operator。这里用来执行生成raw data的脚本。
        task_id='generate_data', #task id在airflow的dashboard中显示的任务名称。这里用来标识生成raw data的任务。
        bash_command=f'python {PATH_TO_DATA_SCRIPT}',
    )
    #Task2
    #task2 任务是在bigquery中创建external tables，连接gcs buzket中的raw data
    create_external_tables_task = BigQueryInsertJobOperator( #BigQueryInsertJobOperator是Airflow中用来执行BigQuery SQL语句的operator。这里用来执行创建external table的SQL语句。
        task_id='create_external_tables', #task id在airflow的dashboard中显示的任务名称。这里用来标识创建external table的任务。
        configuration={
            "query": {
                "query": CREATE_EXTERNAL_TABLES_SQL, #SQL文件内容作为查询语句
                "useLegacySql": False, #使用标准SQL
            }
        },
        location='australia-southeast2', # BigQuery dataset location；project 为 healthcare-demo-2026。
        gcp_conn_id=GCP_CONN_ID, #gcp_conn_id是Airflow中用来连接GCP的连接id。这里用来指定连接GCP的方式。
    )
    #Task3
    #task3 任务是运行dbt tests。测试source.yml和schema.yml中的tests。dbt tests命令会运行所有tests
    dbt_test_raw = BashOperator(
        task_id="dbt_test_raw",
        # 先激活安装了 dbt 的 virtual environment，再运行 source tests。
        # `&&` 表示前一步成功后才执行下一步；`source:*` 选择 dbt project 中定义的所有 sources 的 tests。
        bash_command=(
            "source /usr/local/airflow/dbt_venv/bin/activate && "
            f'dbt test --select source:* --target {TARGET_ENV} '
            f'--vars "schema_name: {TARGET_ENV}_healthcare_data"'
        ),
        # 指定命令执行时所在的 dbt project 目录，使 dbt 能找到 dbt_project.yml 等配置文件。
        cwd="/usr/local/airflow/include/dbt/healthcare_dbt_bigquery_data_pipeline"
        #cwd=current work directory="/usr/local/airflow/dbt/healthcare_dbt_bigquery_data_pipeline"
    )
    #Task4
    #task4 任务是运行dbt models。运行所有models，除了stg_ehr_data模型。stg_ehr_data模型是用来测试dbt的功能的，不需要运行。
    transform=DbtTaskGroup(
        # DbtTaskGroup 是 Cosmos 提供的一个 class。 DbtTaskGroup 的参数名由 Cosmos 的 API 定义
        group_id="transform", #group id在airflow的dashboard中显示的任务组名称。这里用来标识transform任务组。
        profile_config=DBT_CONFIG, #dbt_config是cosmos库中的ProfileConfig对象，用来读取dbt的profiles.yml文件。这里用来指定dbt的profile配置。
        project_config=DBT_PROJECT_CONFIG, #dbt_project_config是cosmos库中的ProjectConfig对象，用来读取dbt的dbt_project.yml文件。这里用来指定dbt的project配置。
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS, #load_mode是cosmos库中的LoadMode枚举类，用来指定dbt运行模式。这里用来指定dbt的运行模式为全量刷新。
            select=['path:models'], #select是cosmos库中的RenderConfig对象的属性，用来指定dbt运行的模型。这里用来指定dbt运行所有以stg_开头的模型。
        )
        
    )

    #call the task
    generate_data_task >> create_external_tables_task>> dbt_test_raw>>transform
dbt_healthcare_pipeline()
#常见的operator有：BashOperator, PythonOperator, EmailOperator, SlackOperator等。
# BashOperator是用来执行bash命令的，
# PythonOperator是用来执行Python函数的，
# EmailOperator是用来发送邮件的，
# SlackOperator是用来发送Slack消息的。
# 也可以自定义operator，比如自定义一个operator来执行dbt命令，或者自定义一个operator来执行Spark作业。