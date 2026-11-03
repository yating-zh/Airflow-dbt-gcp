# Docker Concepts

- **Docker**: The tool for building images and creating and running containers.
- **Dockerfile**: The build instructions that describe how to make an image.
- **Base image**: The starting point specified with `FROM` in a Dockerfile.
- **Image**: A runnable environment template built from a Dockerfile. It can contain operating system files, Python, Airflow, and dependencies.
- **Container**: A running instance of an image, with its own processes and filesystem.

The relationship is:

```text
Dockerfile (instructions, including a base image)
        ↓ Docker builds
Image (environment template)
        ↓ Docker creates and runs
Container (running instance)
```
