# Task 2：从 GCS 文件创建 BigQuery External Tables

Task 2 建立在 Task 1 之上。Task 1 将 synthetic files 上传到 GCS；Task 2 在 BigQuery 中创建 external tables，使这些文件可被查询。数据文件仍然保存在 GCS；这不是 BigQuery load job，也不会把数据复制到 BigQuery-managed storage。

## Task 做什么

```text
Task 1：生成 synthetic files → GCS
                                ↓
Task 2：BigQuery external tables 指向这些 GCS files
```

External table definitions 保存在 BigQuery，但 CSV、newline-delimited JSON 和 Parquet 数据仍在 GCS。

## 前置条件

- Task 1 已成功将三个 `dev/` 文件上传到 GCS。
- Google Cloud project 已启用 billing 和 BigQuery API。
- 自己拥有一个 GCS bucket；当前 project 使用 `healthcare-data-2026-i`。
- 已创建 BigQuery dataset；当前使用 `dev_healthcare_data`。
- bucket 和 BigQuery dataset 的 locations 兼容；尽量选择相同 location。
- 本机已安装 Docker Desktop 和 Astro CLI。

## 步骤 1：创建 SQL file

创建或更新：

```text
include/raw_data_generation/create_external_tables.sql
```

使用自己的 project ID、dataset ID、bucket 名称和 object paths。BigQuery table identifier 格式为：

```text
`project_id.dataset_id.table_id`
```

当前 SQL 创建三张 external tables：

- `patient_data_external`：读取 `dev/patient_data.csv`，格式为 CSV，并跳过 header row。
- `ehr_data_external`：读取 `dev/ehr_data.json`，格式为 newline-delimited JSON。
- `claims_data_external`：读取 `dev/claims_data.parquet`，格式为 Parquet。

当前 SQL 中的配置是：

```text
Project: healthcare-demo-2026
Dataset: dev_healthcare_data
Bucket:  healthcare-data-2026-i
```

确认这些值与实际创建的 resources 一致。必须先创建 dataset；`CREATE EXTERNAL TABLE` 不会创建 dataset。执行前替换 SQL 中任何属于 tutorial 作者的 project 或 bucket。

## 步骤 2：创建 BigQuery dataset

在 Google Cloud Console 中：

1. 打开 BigQuery 并选择 `healthcare-demo-2026` project。
2. 在 Explorer 中点击 project 菜单，然后选择 **Create dataset**。
3. 将 **Dataset ID** 设为 `dev_healthcare_data`。
4. 选择与 GCS bucket 兼容的 location。
5. 创建 dataset。

Airflow 使用的 service account 需要权限来创建 query jobs、在该 dataset 中创建或替换 tables，并读取 GCS objects。请按需授予最小权限；常见组合包括 BigQuery Job User、dataset 级别的 BigQuery Data Editor，以及 bucket 级别的 Storage Object Viewer。

## 步骤 3：配置 Airflow GCP connection

DAG 使用 `gcp_default` 作为默认 connection ID：

```python
GCP_CONN_ID = Variable.get("GCP_CONN_ID", default_var="gcp_default")
```

在本地 Airflow UI 中：

1. 打开 **Admin → Connections → +**。
2. **Connection Id** 填 `gcp_default`。
3. **Connection Type** 选 `Google Cloud`。
4. 如果页面有 project ID 字段，填 `healthcare-demo-2026`。
5. **Keyfile Path** 填 Astro container 内的路径：

   ```text
   /usr/local/airflow/include/gcp/service_account.json
   ```

6. 保存 connection。

JSON key 必须位于 repository 的 `include/gcp/service_account.json`，以便 Astro container 可以访问。不要把 key 内容写入本文或 commit 到 Git；`.gitignore` 已忽略该文件。

本地开发时也可以用 Astro 的 `airflow_settings.yaml` 定义 connection；需参考 Astro 文档，并确保 key path 在 container 中有效。

## 步骤 4：让 DAG 读取并提交 SQL

当前 `dags/healthcare_dag.py` 中需要确认以下实现：

1. 代码使用 `Variable.get(...)`，因此需 import：

   ```python
   from airflow.models import Variable
   ```

2. `BigQueryInsertJobOperator` 的 `configuration["query"]["query"]` 需要 SQL 文本，不是 SQL file path。读取文件内容，例如：

   ```python
   with open(PATH_TO_SQL_SCRIPT, 'r') as file:
       CREATE_EXTERNAL_TABLES_SQL = file.read()
   ```

   然后将 `CREATE_EXTERNAL_TABLES_SQL` 作为 query 传入。

DAG 通过以下依赖定义执行顺序：

```python
generate_data_task >> create_external_tables_task
```

这表示 GCS data generation task 成功后，才运行创建 external tables 的 task。

同时确认：

- SQL 中的 GCS 和 BigQuery project IDs 属于自己。
- GCS URIs 指向自己的 bucket 和 `dev/` objects。
- operator 的 `location` 与 BigQuery dataset location 一致。
- `gcp_conn_id` 指向已创建的 connection（默认 `gcp_default`；若设置了 `GCP_CONN_ID` Airflow Variable，则需匹配该 connection ID）。

## 步骤 5：build 并启动本地 Airflow

如果修改了 `Dockerfile` 或 dependencies，需要重新 build image。从 repository root 执行：

```bash
docker info
astro dev build
astro dev start
```

如果 image 已构建成功，之后只修改 DAG 或 SQL file，Astro 通常会自动检测运行环境中的 DAG 改动。也可以显式重启：

```bash
astro dev restart
```

打开 Astro CLI 显示的本地 Airflow UI 地址，通常为 `http://localhost:8080`，并使用本地 Airflow credentials 登录。

## 步骤 6：运行并验证 DAG

1. 在 Airflow UI 中确认 healthcare DAG 可见且没有 import error。
2. 手动 trigger DAG，或等待 daily schedule。
3. 确认 `generate_data` 成功，且 GCS 的 `dev/` 下存在三个 files。
4. 确认 `create_external_tables` 成功。
5. 在 BigQuery Explorer 打开 `dev_healthcare_data`，确认存在：
   - `patient_data_external`
   - `ehr_data_external`
   - `claims_data_external`
6. 执行小型 query，例如：

   ```sql
   SELECT *
   FROM `healthcare-demo-2026.dev_healthcare_data.patient_data_external`
   LIMIT 10;
   ```

如果 query 返回 rows，说明 BigQuery 能读取 GCS file；rows 的数据来源仍是 GCS。

## 重要安全提醒

DAG 会先运行 Task 1，再创建 external tables。generator 每次运行都会清空 GCS 的 `dev/` 和 `prod/` prefixes，然后生成新数据。不要对需要保留的 objects 运行。`@daily` schedule 表示 DAG 可每天运行；不需要自动更新时，可以 pause DAG。

## 常见错误排查

### DAG import error：`NameError: name 'Variable' is not defined`

添加：

```python
from airflow.models import Variable
```

### BigQuery job 把 file path 当作 SQL 或拒绝 query

operator 需要 `create_external_tables.sql` 的文件内容，而不是文件系统 path。读取 SQL file 为 string，再把 string 作为 query 传入。

### Airflow 提示缺少 `gcp_default` connection

在 **Admin → Connections** 创建 Google Cloud connection，或设置 `GCP_CONN_ID` Airflow Variable 指向已有 connection ID。

### GCP permission error

Authentication 和 authorization 是两回事。确认 service account key 有效，并且 service account 有：

- 创建 BigQuery jobs 的权限。
- 在目标 dataset 创建或替换 tables 的权限。
- 读取 GCS objects 的权限。

### BigQuery 无法读取 GCS URI

检查 project、bucket、object path 和文件是否存在。确认 BigQuery 有权读取 bucket，并确认 dataset 和 bucket locations 兼容。

### External table 或 query 报 location mismatch

将 DAG 中 BigQuery job 的 `location` 设成 dataset location，并确认 GCS 外部数据位置与该 dataset 兼容。

### `CREATE OR REPLACE EXTERNAL TABLE` 报名称当前是 `TABLE`

BigQuery 可能返回类似错误：

```text
... is not allowed for this operation because it is currently a TABLE
```

说明目标名称已被 BigQuery-managed table 占用。即使 managed table 是空的，`CREATE OR REPLACE EXTERNAL TABLE` 也不能把它替换成 external table。

执行 SQL 前：

1. 不要手动创建与 external tables 同名的空 managed tables。
2. 检查 dataset 是否有名称冲突。
3. 如果已有 managed table 不需要保留，先在 BigQuery 删除；否则给 external table 使用新名称，例如 `patient_data_gcs_external`。
4. 解决名称冲突后重试 `create_external_tables`。

如果 `generate_data` 已成功且 GCS files 已存在，尽量只重试失败的 `create_external_tables` task。重跑整个 DAG 会再次清空并重建 GCS 的 `dev/` 和 `prod/` objects。

### Airflow 或 task logs 报错

```bash
astro dev logs --webserver
astro dev logs --scheduler
```

task 专属错误可在 Airflow UI 打开对应 task instance 并查看 log。

## 当前范围和下一步

此 task 创建可查询 GCS files 的 BigQuery external tables。它不会把数据 load 到 BigQuery-managed tables，也不会运行 dbt transformations。后续 task 可以用 BigQuery load jobs 创建 managed raw tables，再对这些 tables 运行 dbt models。
