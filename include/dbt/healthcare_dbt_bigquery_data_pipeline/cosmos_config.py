from cosmos.config import ProfileConfig, ProjectConfig
from pathlib import Path

DBT_CONFIG = ProfileConfig(
    profile_name='healthcare_dbt_bigquery_data_pipeline',
    target_name='prod',
    #target_name='dev',
    profiles_yml_filepath=Path('/usr/local/airflow/include/dbt/healthcare_dbt_bigquery_data_pipeline/profiles.yml')
    #profiles.yml file path
)

DBT_PROJECT_CONFIG = ProjectConfig(
    dbt_project_path='/usr/local/airflow/include/dbt/healthcare_dbt_bigquery_data_pipeline/'
    #dbt_project.yml file path
)

#这个cosmos_config.py文件是用来配置dbt的profile和project的路径的。ProfileConfig和ProjectConfig是cosmos库中的两个类，用来读取dbt的配置文件。DBT_CONFIG是一个ProfileConfig对象，DBT_PROJECT_CONFIG是一个ProjectConfig对象。
#只有设置了DBT_CONFIG和DBT_PROJECT_CONFIG，才能在dag中使用dbt的功能，比如运行dbt models，运行dbt tests等。
#task1和2都不需要dbt的功能，所以不需要DBT_CONFIG和DBT_PROJECT_CONFIG。task3需要运行dbt tests，所以需要DBT_CONFIG和DBT_PROJECT_CONFIG。