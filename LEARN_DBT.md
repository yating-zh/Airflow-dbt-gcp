# dbt YAML 文件

dbt 使用 YAML 文件配置 project、描述数据并声明 data tests。这个 project 中的文件职责如下：

| 文件 | 用途 |
|---|---|
| `dbt_project.yml` | dbt project 的主配置，包括 project 名称、使用的 profile、models 等资源目录，以及 model materialization 默认值。本 project 默认值为 `view`。 |
| `profiles.yml` | 配置 dbt 连接 BigQuery 的环境，包括 project、dataset、location、认证方式和 target。 |
| `models/sources.yml` | 声明输入的 raw data sources（例如 BigQuery source tables），并可描述它们、定义 source data tests。 |
| `models/schema.yml` | 描述 dbt models 及其 columns，并定义 model data tests，例如 `not_null`、`unique` 和 `accepted_values`。 |
| `packages.yml` | 声明 project 使用的外部 dbt packages。本 project 声明 `dbt-labs/dbt_utils` 1.3.0；运行 `dbt deps` 安装依赖。 |
| `.user.yml` | 当前包含 UUID，似乎是工具生成的 project/user metadata。它不是 BigQuery connection、models 或 tests 的核心配置，通常不需要手动编辑。 |

## 快速记忆

```text
dbt_project.yml → dbt project 如何组织和运行
profiles.yml    → dbt 连接哪个 BigQuery 环境
sources.yml     → 输入的 raw data 在哪里
schema.yml      → model 描述和 data tests
packages.yml    → project 依赖的外部 dbt packages
```

## Source tests 和 model tests

- `sources.yml` 声明并可测试上游 raw data。
- `schema.yml` 描述并可测试 dbt models。
- Tests 检查数据是否符合声明的规则；失败时会报告问题，不会清理或修改数据。
- 自定义 SQL tests 通常放在 `tests/` 目录。

## 当前 project 配置

当前 project 使用：

```text
GCP project: healthcare-demo-2026
BigQuery dataset: dev_healthcare_data
BigQuery location: australia-southeast2
GCS bucket: healthcare-data-2026-i
```

`profiles.yml` 中的 `dev` 和 `prod` outputs 都配置为 project `healthcare-demo-2026`、location `australia-southeast2`；默认 target 是 `dev`。运行前仍应确认 BigQuery dataset 的实际 location 与 profile 一致。

Cosmos 的 `cosmos_config.py` 也指定 `target_name='dev'`。因此当前 Cosmos `transform` task 和未显式传 `--target` 的 dbt 命令都以 `dev` 为目标。若要运行到其他环境，应先确认 target 和目标 dataset，避免在不期望的环境创建或更新对象。

同时确认 `models/sources.yml` 中的 project ID、dataset 名称和 source table 名称都与 BigQuery 中实际存在的 external tables 一致。
