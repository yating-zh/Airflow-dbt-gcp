# 使用过的命令

本文记录设置 Astro project、检查 Docker、安装 Python dependencies、测试 GCS、运行 data generator 和检查 Git branches 时使用的命令。更新日期：2026-11-02。

## Astro 和 Docker

1. `docker --version` — 查看 Docker CLI 版本，结果为 `29.8.2`。
2. `docker info` — 检查 Docker Engine；最初返回 HTTP 500，稍后恢复正常。
3. `astro version` — 最初提示 `command not found`；之后显示 Astro CLI 版本 `1.46.1`。
4. `astro --version` — 返回 `command not found`。
5. `astro dev init` — 初始化 Astro project。
6. `astro start` — 失败，因为 `start` 不是 Astro CLI 的顶层 command。
7. `astro dev start` — 多次尝试启动；早期因 Docker 不可用或无法访问 iCloud Drive 下的 project folder 而失败，之后启动成功。

## Python environment 和 GCS

以下命令从 project root 执行：

1. `python --version` — 显示 Python `3.10.8`。
2. `python3 -m venv .venv` — 创建 project 的本机 virtual environment。
3. `source .venv/bin/activate` — 激活 virtual environment。
4. `python -m pip install google-cloud-storage` — 安装 GCS client library。
5. `python -m pip install -r requirements.txt` — 安装 `requirements.txt` 中列出的 dependencies。
6. `python -m pip install pandas numpy faker pyarrow` — 安装 data generation dependencies。
7. `python -c "from google.cloud import storage; print('ok')"` — 检查是否可以 import GCS library。
8. 使用 `/usr/local/airflow/include/gcp/service_account.json` 测试 credentials 时，在本机因 `FileNotFoundError` 失败；这是 container path，不是 Mac 本机路径。
9. 使用 `include/gcp/service_account.json` 测试 credentials 时打印了 `Connected`，表示 authentication 成功。
10. `./.venv/bin/python include/raw_data_generation/healthcare_data.py` — 生成 synthetic data，并将 CSV、newline-delimited JSON、Parquet 上传到 GCS。脚本上传前会清空 `dev/` 和 `prod/` prefixes。

## Git branch 检查

1. `git status --short --branch` — 查看当前 branch 和 working tree 改动。
2. `git branch --show-current` — 查看当前 branch 名称。
3. `git remote -v` — 查看配置的 GitHub remote。
4. `git --no-pager log --oneline --decorate --graph --all -8` — PR merge 后查看最近 commits 和 branches 的位置。

## 补充说明

- VS Code 中的 `Python: Select Interpreter` 是 Command Palette command，不是 shell command。
- data generator 使用 service account JSON 作为 credential。不要提交或分享这个文件。
- Airflow DAG import 曾因当前版本不接受 `schedule_interval` 而失败；当前 `@dag` decorator 使用 `schedule`。
