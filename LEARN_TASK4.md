# Task 4：用 Cosmos 运行 dbt Models

Task 4 使用 Astronomer Cosmos 的 `DbtTaskGroup`，将 dbt project 中选中的 models 转成 Airflow tasks，并运行它们。与 Task 3 的 source tests 不同，Task 4 会执行 SQL transformations，并在 BigQuery 中创建或更新 model relations。

## Data flow

```text
GCS raw files
    ↓
BigQuery external tables（dbt sources）
    ↓
Task 4：dbt models
    ↓
BigQuery model tables
```

Task 4 依赖前面的数据生成、external table 创建和 source tests 成功完成。

## 当前 DAG 的 Cosmos 配置

`dags/healthcare_dag.py` 中的 `transform` 使用 `DbtTaskGroup`：

- `profile_config=DBT_CONFIG`：提供 Cosmos 使用的 dbt profile。
- `project_config=DBT_PROJECT_CONFIG`：指定 dbt project。
- `render_config` 中的 `select=['path:models']`：选择 `models/` 路径下的 dbt resources。
- `load_method=LoadMode.DBT_LS`：让 Cosmos 使用 dbt 的 `dbt ls` 读取 project 节点并生成 Airflow tasks。

`DbtTaskGroup` 是 Cosmos 的 class；它会为选中的 dbt resources 创建一个 Airflow task group。Airflow UI 中展开 `transform`，可以看到每个 model 对应的运行 task 和 test task。

## 当前 dbt Models

`include/dbt/healthcare_dbt_bigquery_data_pipeline/models/` 下有 5 个 model SQL：

| Model                        | 大致用途              |
| ---------------------------- | --------------------- |
| `chronic_conditions_summary` | 汇总慢性疾病数据      |
| `patient_demographics`       | 汇总患者人口统计信息  |
| `claims_status_summary`      | 汇总 claim 状态和金额 |
| `health_anomalies`           | 标记生命体征异常      |
| `high_claim_patients`        | 筛选高额 claims 患者  |

Model 的 SQL 是项目源代码，不是 dbt 自动生成的文件。dbt 编译并执行 SQL 后，结果 relation 才会出现在 BigQuery。

## Model 会生成 Table 还是 View

虽然 `dbt_project.yml` 将默认 materialization 设为 `view`，但目前这 5 个 model SQL 都通过 `{{ config(materialized='incremental', ...) }}` 单独设置为 `incremental`。因此它们成功运行后，通常会在目标 BigQuery dataset 中创建或更新 tables，而不是默认 views。

在 BigQuery Console 中选择 project `healthcare-demo-2026`，展开当前 target 对应的 dataset：

- `dev` target → `dev_healthcare_data`
- `prod` target → `prod_healthcare_data`

然后查看与 model 文件名对应的 relations。Airflow 中 model 的 `.run` task 成功，表示该 model 的执行成功；对应的 `.test` task 是另外的测试步骤，需分别查看状态。

## 环境选择

Cosmos 的 profile target 由 `include/dbt/healthcare_dbt_bigquery_data_pipeline/cosmos_config.py` 中的 `DBT_CONFIG.target_name` 决定：

- `target_name='dev'`：模型使用 `profiles.yml` 中 dev output，目标 dataset 为 `dev_healthcare_data`。
- `target_name='prod'`：模型使用 prod output，目标 dataset 为 `prod_healthcare_data`。

当前 project 的 GCP project 是 `healthcare-demo-2026`，BigQuery location 是 `australia-southeast2`。运行 prod 前要确认目标 dataset、权限和 DAG 中 Task 1–3 的环境选择都一致。

## 查看失败原因

在 Airflow UI 中展开 `transform`，点击具体失败的 `.run` 或 `.test` task，再打开该 task instance 的 Logs：

- `.run` 失败：查看 dbt 编译、BigQuery SQL、source 依赖或权限错误。
- `.test` 失败：查看具体 test；例如 `not_null` 失败时，可在 BigQuery 查询对应 column 的 `NULL` records。
- `transform` 父级 TaskGroup 的 Event Log 只汇总事件；要看详细错误，需要打开具体子 task 的 Logs。

若日志显示 dbt selector 错误，应检查 `select` / `exclude` 使用的 dbt selector method 是否有效，以及所选 model 是否存在。
