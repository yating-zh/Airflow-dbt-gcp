# Task 3：用 dbt 检查 Source Data

Task 3 在 BigQuery external tables 创建后，运行 dbt 的 source tests，检查输入的 raw data 是否符合规则。

## Data flow

```text
GCS raw files
    ↓
BigQuery external tables
    ↓
Task 3：dbt test --select source:*
```

Source tests 只检查数据，不会创建或转换 dbt models，也不会修复源数据。

## 当前 DAG 的实现

`dags/healthcare_dag.py` 中的 `dbt_test_raw` 是一个 `BashOperator`。它会：

1. 激活 `/usr/local/airflow/dbt_venv` 中安装的 dbt。
2. 在 dbt project directory 中运行 `dbt test --select source:*`。
3. 把 `DBT_CONFIG.target_name` 作为 dbt `--target`。
4. 通过 `--vars` 把 `schema_name` 设成 `<target>_healthcare_data`。

例如，当 `cosmos_config.py` 中的 `target_name` 为 `prod`，Task 3 的目标是：

```text
dbt target: prod
source dataset: prod_healthcare_data
```

当 target 为 `dev`，source dataset 则是 `dev_healthcare_data`。`--target` 选择 `profiles.yml` 中的连接配置；`--vars` 覆盖 `sources.yml` 中的 `schema_name`，两者作用不同。

## Source tests 写在哪里

当前 raw source 定义和 tests 位于：

```text
include/dbt/healthcare_dbt_bigquery_data_pipeline/models/sources.yml
```

例如：

- `not_null`：检查 column 是否有 `NULL`。
- `unique`：检查 column 值是否重复。

这份文件将 sources 组织在 `healthcare_data` source 下，包括 `patient_data_external`、`ehr_data_external` 和 `claims_data_external`。

## 查看运行结果

在 Airflow UI 中打开 `dbt_test_raw` task 的 Logs。成功的测试会显示 `PASS`；失败的测试会显示 `FAIL` 或 database error。Task 失败时，要区分：

- **Test failure**：查询成功，但数据不符合规则。
- **Database/compilation error**：dbt 无法连接 BigQuery、找不到表或配置有误，测试可能还没真正检查数据。

如果 `not_null` test 失败，可在 BigQuery 中直接查询问题记录。例如检查 prod external table：

```sql
SELECT *
FROM `healthcare-demo-2026.prod_healthcare_data.claims_data_external`
WHERE claim_amount IS NULL;
```

检查 dev 时，把 dataset 改成 `dev_healthcare_data`。先确认 task 实际使用的 target 和 source dataset，避免查询错环境。

## 前置条件和注意事项

- Task 1 和 Task 2 必须先成功，确保 GCS files 和相应环境的 BigQuery external tables 已准备好。
- dbt dependencies 必须已安装。Cosmos 的 dbt task 日志可能显示它先执行 `dbt deps`；也可以进入 container，在 dbt project directory 手动运行 `dbt deps`。
- `sources.yml` 的 source project、dataset、table 名称必须与 BigQuery 实际对象一致。
- 当前 project 使用 GCP project `healthcare-demo-2026`，BigQuery location 为 `australia-southeast2`。
- Airflow 中可以只对 dev 执行 tests，也可以对 prod 执行；是否运行由 DAG 的依赖和 target 配置决定，不是 dbt 的限制。
