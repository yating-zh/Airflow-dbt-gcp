# 什么是 DAG？

- **DAG** 描述一组逻辑相关的 tasks，包括它们什么时候运行、以什么顺序运行。
- **Schedule** 决定 DAG run 什么时候开始。
- **Task dependencies** 决定一个 DAG run 中，哪个 task 必须先完成，另一个 task 才能开始。

## 示例一：互相独立的 Finance 和 Customer reports

可以创建两个 DAG，并都设置为每天早上 8 点运行：

```text
finance_report_dag   → 生成 Finance report
customer_report_dag  → 生成 Customer report
```

它们可以分别 schedule、monitor 和管理。但不保证它们恰好同时运行：Airflow concurrency limits 或对共享 resources 的竞争可能影响启动时间。

## 示例二：有顺序的 data pipeline

生成 CSV、上传到 GCS、再 load 到 BigQuery，通常作为同一个 DAG 中的 tasks，并通过 dependencies 表示顺序：

```text
generate_csv_task → upload_to_gcs_task → load_to_bigquery_task
```

每个 task 等待前一个 task 成功后才运行。三个 tasks 组成一个 DAG run，并根据 DAG 的 schedule 开始，例如每天早上 8 点。

## Tasks 也可以并行运行

不是每个 task 都要放进独立 DAG 才能并行。同一个 DAG 中没有 dependency 关系的 tasks 可以并行运行。若 workflows 的业务目的、schedule、owner 或 monitoring 需求不同，通常更适合拆成不同 DAG。
