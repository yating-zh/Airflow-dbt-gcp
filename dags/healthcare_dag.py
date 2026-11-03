# Import DAG decorator and BashOperator
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
# Pendulum is a Python date-and-time library that handles time zones cleanly. Airflow uses it for dates such as a DAG’s start_date.
from pendulum import datetime

PATH_TO_DATA_SCRIPT = '/usr/local/airflow/include/raw_data_generation/healthcare_data.py'
@dag(schedule='@daily', 
     start_date=datetime(2026, 1, 1), 
     catchup=False, 
     tags=['healthcare'], 
     description='healthcare data pipeline',
     doc_md=__doc__,) #doc_md是DAG的文档说明，可以用来描述DAG的功能和用途。这里用__doc__表示使用当前文件的文档字符串作为DAG的文档说明。

#ddbt_healthcare_pipeline 是 dag function的名字，用来定义一个dag。dag function是一个Python函数，里面可以定义多个task。每个task都是一个operator，用来执行具体的操作。dag function的返回值是一个DAG对象，表示整个dag的结构和依赖关系。
def dbt_healthcare_pipeline():
    #generate_data_task 是 dag function中的一个task
    generate_data_task = BashOperator( #bashOperator是Airflow中用来执行bash命令的operator。这里用来执行生成raw data的脚本。
        task_id='generate_data', #task id在airflow的dashboard中显示的任务名称。这里用来标识生成raw data的任务。
        bash_command=f'python {PATH_TO_DATA_SCRIPT}',
    )
    #call the task
    generate_data_task
dbt_healthcare_pipeline()
#常见的operator有：BashOperator, PythonOperator, EmailOperator, SlackOperator等。
# BashOperator是用来执行bash命令的，
# PythonOperator是用来执行Python函数的，
# EmailOperator是用来发送邮件的，
# SlackOperator是用来发送Slack消息的。
# 也可以自定义operator，比如自定义一个operator来执行dbt命令，或者自定义一个operator来执行Spark作业。