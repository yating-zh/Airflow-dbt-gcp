# 为本 Project 创建 GCP Service Account

本文记录如何为 `include/raw_data_generation/healthcare_data.py` 配置 GCP access。

## 1. 不要复用别人的 JSON key

不要直接使用 tutorial 或其他 repository 中的 service account JSON。它绑定到原拥有者的 Google Cloud project、permissions、bucket 和账号。复用可能造成权限错误、访问错误 project、泄露安全风险或误访问他人数据。请使用自己的 GCP project 和 service account。

## 2. 创建 GCP project

1. 打开 <https://console.cloud.google.com/>。
2. 选择或创建 project。
3. 为 project 命名，例如 `healthcare-demo-2026`。
4. 记下 project ID。

## 3. 启用 APIs

至少启用：

- Cloud Storage API

之后使用 BigQuery 时还要启用：

- BigQuery API

启用步骤：进入 `APIs & Services` → `Library`，搜索所需 API，然后点击 `Enable`。

## 4. 创建 service account

1. 进入 `IAM & Admin` → `Service Accounts`。
2. 点击 `Create Service Account`。
3. 设置名称，例如 `airflow-gcs-sa`。
4. 点击 `Create and Continue`。
5. 添加所需 roles，然后点击 `Done`。

## 5. 授予 permissions

当前 data generator 需要 service account 能够：

- list buckets
- create 或检查 bucket
- list bucket objects
- 上传 objects 到 GCS
- 删除 GCS objects

学习环境中较简单的选择是 `Storage Admin`。也可以组合使用更细粒度的 `Storage Object Admin` 和 `Storage Bucket Admin`。后续若要访问 BigQuery，还需授予对应 BigQuery permissions；优先选择满足任务需要的最小权限。

## 6. 创建 JSON key

1. 打开 service account。
2. 进入 `Keys`。
3. 点击 `Add Key` → `Create new key`。
4. 选择 `JSON` 并下载文件。

请将此文件当作 secret：不要 commit 到 Git、不要放进公开 repository，也不要在截图或聊天中分享。

## 7. 放置 JSON key

在 repository 中将文件放到：

```text
include/gcp/service_account.json
```

运行在 Astro container 中时，同一个 project 文件会位于：

```text
/usr/local/airflow/include/gcp/service_account.json
```

原 tutorial 使用了 container-only path；本机 Mac 应使用 project 内的文件路径。当前 generator 会检查 `GOOGLE_APPLICATION_CREDENTIALS`、container path 和相对脚本的候选路径。

## 8. 确认 `.gitignore`

repository 的 `.gitignore` 已包含类似规则：

```gitignore
**/service_account.json
```

运行 `git status`，确认 JSON key 没有出现在待提交文件中。

## 9. 创建并激活本机 Python virtual environment

在 project root 执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install google-cloud-storage pandas numpy faker pyarrow
```

## 10. 验证 credentials

使用本机文件的实际路径测试 GCS authentication：

```bash
python -c "from google.cloud import storage; c = storage.Client.from_service_account_json('/path/to/project/include/gcp/service_account.json'); print('Connected')"
```

打印 `Connected` 表示 credentials 可以用于 authentication；它不代表 service account 已获得所有 GCS permissions。

## 11. 运行 data generator

从 project root 执行：

```bash
./.venv/bin/python include/raw_data_generation/healthcare_data.py
```

脚本会检查或创建 bucket、清空 `dev/` 和 `prod/` prefixes、生成 synthetic healthcare data，再上传 CSV、JSON Lines 和 Parquet 文件。每次运行都会删除两个 prefixes 下的现有 objects，执行前先确认数据可以被替换。

## 12. 排查常见错误

### 凭证文件找不到

检查文件是否在 `include/gcp/service_account.json`。`/usr/local/airflow/...` 是 Astro container path，本机 Mac 不一定存在。

### GCS 返回 `403 Forbidden`

如果报错包含 `storage.buckets.get` 或 `storage.objects.list`，表示 authentication 识别了 service account，但 IAM 没有授权它访问目标 bucket。确认 `BUCKET_NAME` 是自己的 bucket，并检查该 service account 在 project 或 bucket 上的 Storage roles。

### 使用了 tutorial 作者的 bucket

教程中的 bucket 属于其他 project。把脚本中的 `BUCKET_NAME` 改为你自己的 bucket，并确认 bucket 名称全局唯一。

## 最后检查清单

1. 使用自己的 GCP project。
2. 使用自己的 service account 和 JSON key。
3. 把 key 放在 `include/gcp/service_account.json`。
4. 确认 key 被 `.gitignore` 忽略。
5. 为 service account 授予必要的 Storage permissions。
6. 在本机 virtual environment 中安装 dependencies。
7. 确认 bucket 名称后再运行 generator。
