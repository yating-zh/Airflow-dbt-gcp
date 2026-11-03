# Docker 概念

- **Docker**：用于构建 images、创建和运行 containers 的工具。
- **Dockerfile**：描述如何制作 image 的构建规则。
- **Base image**：Dockerfile 通过 `FROM` 指定的构建起点。
- **Image**：根据 Dockerfile 构建出的可运行环境模板，可包含 operating system files、Python、Airflow 和 dependencies。
- **Container**：运行中的 image instance，拥有自己的 processes 和 filesystem。

它们之间的关系：

```text
Dockerfile（构建规则，包含 base image）
        ↓ Docker 根据规则构建
Image（环境模板）
        ↓ Docker 创建并运行
Container（运行中的 instance）
```

在本 project 中，Astro CLI 会调用 Docker 来构建 project image 并启动本机 Airflow containers。容器里的 `/usr/local/airflow/...` 是 container filesystem path，不是 Mac 上的 project directory。
