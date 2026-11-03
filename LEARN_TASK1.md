# Task 1：生成 Synthetic Healthcare Data 并上传到 GCS

本文记录如何复刻当前 task：生成 synthetic healthcare data、上传到 GCS，并通过本机 Airflow DAG 运行 generator。

> 这些 records 由 Faker 和 Python random functions 生成，不来自医院、真实数据库或真实患者。`prod/` 只是 tutorial 中较大规模的 sample，不代表真实 production data。

## Task 做什么

```text
Airflow DAG
    ↓ 运行 BashOperator task
healthcare_data.py
    ↓ 生成随机 patient、EHR 和 claims records
GCS bucket
    ├── dev/
    │   ├── patient_data.csv
    │   ├── ehr_data.json
    │   └── claims_data.parquet
    └── prod/
        ├── patient_data.csv
        ├── ehr_data.json
        └── claims_data.parquet
```

脚本为 `dev/` 生成 5,000 条 records，为 `prod/` 生成 20,000 条。每次运行前都会删除两个 prefixes 下的现有 objects，再上传新数据。不要对需要保留的数据运行此脚本。

本 task 到 GCS 为止；还没有把数据 load 到 BigQuery，也没有运行 dbt。

## 前置条件

- 已创建自己的 Google Cloud project，并启用 Cloud Storage API。
- 已创建自己的 GCS bucket；当前 project 使用 `healthcare-data-2026-i`。
- service account 有权限列出所需 buckets、创建/检查 bucket、列出/上传/删除 objects。
- 本机已安装 Docker Desktop 和 Astro CLI，用于运行本地 Airflow。
- 本机有 Python 3，用于直接运行和测试 generator。

GCP budget alerts 只是通知，不是硬性消费上限。使用 cloud services 前请检查可能产生的费用并设置 billing alerts。

## 步骤 1：准备 service account credentials

1. 在 Google Cloud Console 中选择自己的 project 并启用 Cloud Storage API。
2. 创建专用 service account，例如 `airflow-gcs-sa`。
3. 授予所需 Storage permissions。学习环境中可用 project-level `Storage Admin`，但它的权限范围较广。
4. 为 service account 创建并下载 JSON key。
5. 在 repository 中创建目录（如果尚不存在）：

   ```text
   include/gcp/
   ```

6. 将 JSON key 放在此目录并命名为：

   ```text
   include/gcp/service_account.json
   ```

7. 保持 key 秘密。repository 的 `.gitignore` 会忽略 `service_account.json`；不要 commit、复制进 source code，或在聊天和截图中分享。

generator 会依次检查 `GOOGLE_APPLICATION_CREDENTIALS`、常见 Astro container path 和相对于脚本的路径来定位 key。

## 步骤 2：创建 data-generation script

创建：

```text
include/raw_data_generation/healthcare_data.py
```

可参考 [原 tutorial repository](https://github.com/ChuquEmeka/Airflow-dbt-bigquery-gcs-healthcare-data-pipeline/blob/main/include/raw_data_generation/healthcare_data.py)，并保留本 project 添加的本机 credential path 处理逻辑。

检查脚本开头附近的设置：

- `BUCKET_NAME` 必须是自己拥有的 bucket；当前设置为 `healthcare-data-2026-i`。
- 本机运行时 credentials 应能解析到 `include/gcp/service_account.json`；Astro container 中的 path 为 `/usr/local/airflow/include/gcp/service_account.json`。
- GCS client 必须使用自己的 service account JSON key 创建。

脚本生成 patient demographics CSV、newline-delimited JSON 格式的 EHR records，以及 Parquet 格式的 claims data。

## 步骤 3：设置本机 Python environment

在 repository root 执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pandas numpy Faker pyarrow
```

当前 `requirements.txt` 列出 `google-cloud-storage`；直接在 Mac 本机运行 generator 时还需要安装其他数据生成 dependencies。

验证 GCS package 可以 import：

```bash
./.venv/bin/python -c "from google.cloud import storage; print('GCS client import works')"
```

## 步骤 4：直接测试 generator

从 repository root 执行：

```bash
./.venv/bin/python include/raw_data_generation/healthcare_data.py
```

检查输出是否包含：

- 选择到的 credentials path。
- `Successfully connected to GCS`。
- 可访问 bucket 列表中的自己的 bucket 名称。
- `dev/` 和 `prod/` 的文件上传成功信息。
- `Data generation and upload to GCS completed successfully.`。

此命令会实际修改 GCS，并在上传前删除 `dev/` 和 `prod/` prefixes 下已有的 objects。

## 步骤 5：配置 Astro Runtime image

当前 project 的 Dockerfile 使用 Astro Runtime 12.7.1，并在 container 中安装 dbt 和 generator dependencies：

```dockerfile
FROM quay.io/astronomer/astro-runtime:12.7.1
```

Dockerfile 在 container 内创建独立 virtual environment，并安装 `dbt-bigquery==1.9.2`、pandas、Faker、PyArrow 和 NumPy。这些与 Mac 上的 `.venv` 是不同环境。

构建 image：

```bash
astro dev build
```

确认 build 成功后再启动 Airflow。

## 步骤 6：定义 Airflow DAG

创建或更新：

```text
dags/healthcare_dag.py
```

当前 DAG：

- import `dag` 和 `BashOperator`。
- 使用 `schedule='@daily'`、`catchup=False`。
- 定义 `generate_data` task，运行 `/usr/local/airflow/include/raw_data_generation/healthcare_data.py`。
- 在 module level 调用 DAG factory，让 Airflow 能发现 DAG。

container path 必须是 `/usr/local/...`（`usr`，不是 `user`）。`BashOperator` 在创建时就注册为 task；单独写一行 task variable 不会执行 task，也不会定义顺序。

## 步骤 7：启动本地 Airflow 并运行 task

确保 Docker Desktop 正在运行，然后从 repository root 执行：

```bash
docker info
astro dev start
```

打开 Astro CLI 输出的本地 Airflow UI 地址，通常是 `http://localhost:8080`，并使用本地 Airflow credentials 登录。

1. 找到 `healthcare` DAG，确认没有 import error。
2. 可手动 trigger DAG 进行学习，或等待 daily schedule。
3. 打开 `generate_data` task logs，确认 GCS upload 成功。
4. 在 bucket 中确认 `dev/` 和 `prod/` 下各有三个文件。

trigger 前先检查 bucket。此 task 每次运行都会清空 `dev/` 和 `prod/` prefixes。

## 常见错误排查

### `ImportError: cannot import name 'storage' from 'google.cloud'`

当前 Python environment 缺少 GCS library。需要在运行命令的同一个 environment 安装：

```bash
./.venv/bin/python -m pip install google-cloud-storage
```

### `ModuleNotFoundError` 找不到 pandas、Faker、PyArrow 或 NumPy

在本机 `.venv` 中安装 generator dependencies：

```bash
./.venv/bin/python -m pip install pandas numpy Faker pyarrow
```

### `FileNotFoundError` 指向 `/usr/local/airflow/.../service_account.json`

这是 container path，本机 Mac 上可能不存在。确认本机 key 位于 `include/gcp/service_account.json`，并确认脚本会相对于 `healthcare_data.py` 解析本机路径。

### GCS `403 Forbidden`，例如 `storage.buckets.get` 或 `storage.objects.list`

Authentication 成功，但 service account 没有访问 bucket 或 project 的授权。确认：

- `BUCKET_NAME` 是自己的 bucket，而不是 tutorial 作者的 bucket。
- JSON key 对应的 service account 在 project 或 bucket 上拥有必要的 Storage roles。
- IAM permission 更新已生效。

### Docker 返回 `500 Internal Server Error`

Docker CLI 可运行，但 Docker Engine 没响应。重启 Docker Desktop，等待 Engine 启动，确认 `docker info` 能显示 Server 信息，然后检查：

```bash
astro dev ps
```

如果没有列出 containers，再运行 `astro dev start`。

### build image 时 `cffi` 编译报 `No such file or directory: 'cc'`

此问题曾出现在 Astro Runtime 3.3-11（Python 3.14）与较旧的 `dbt-bigquery==1.5.3` 组合中：dependency 尝试编译 `cffi`，但 image 中没有 compiler。当前 project 使用 Astro Runtime 12.7.1（Python 3.12）和 `dbt-bigquery==1.9.2`。优先让 Runtime 和 dbt versions 兼容，不要先用添加 compiler 来绕过。

### Airflow 提示 metadata database 需要 upgrade，或出现 `execution_date` error

切换 Astro Runtime/Airflow version 后继续使用旧的本地 Postgres metadata database，可能导致不兼容。如果不需要本地 Airflow history、connections、variables 和 task logs，可以用 `astro dev kill` 重置本地 environment；它会删除这些数据。需要保留时不要运行。

### DAG import error：`schedule_interval` 是 unexpected keyword

当前 `@dag` decorator 应使用 `schedule='@daily'`。

### task 找不到 `healthcare_data.py`

检查 DAG 使用的 container path：

```text
/usr/local/airflow/include/raw_data_generation/healthcare_data.py
```

task 在 container 中运行，不是直接从 Mac 的 project path 运行。

### 查看 Airflow logs

```bash
astro dev logs --webserver
astro dev logs --scheduler
```

## 当前范围和下一步

此 task 生成 synthetic raw files 并上传到 GCS。当前 DAG 还没有将数据 load 到 BigQuery，也没有运行 dbt。后续可以增加 GCS-to-BigQuery loading、raw tables 和 dbt transformations。
