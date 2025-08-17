# AGENTS.md (For Jules)
<!-- This file is optimized for consumption by the Jules coding agent. -->
<!-- It focuses on project-specific context, commands, and conventions. -->

## 1. Project Overview & Goal

This repository contains the source code for "My Trading App," a high-throughput, low-latency data pipeline for cryptocurrency market data. The system architecture is service-oriented, containerized with Docker, and orchestrated by Docker Compose. The canonical architectural document is `PROJECT_BLUEPRINT_V2.5.md`.

## 2. Core Commands & Toolchain

The primary toolchain for this project is `docker compose`. All testing, linting, and dependency management operations are executed within Docker containers.

-   **To run all linters and formatters:**
    ```bash
    docker compose run --rm lint
    ```

-   **To run the complete test suite (unit and integration):**
    ```bash
    docker compose run --rm test
    ```

-   **To start the development environment:**
    ```bash
    make dev-up
    ```

## 3. Dependency Management Conventions

Dependencies are managed via `pyproject.toml` and installed with `uv`. There are two types of dependency files:
1.  **Shared:** `/src/shared/pyproject.toml` for libraries used by multiple services.
2.  **Service-Specific:** e.g., `/src/services/receiver/pyproject.toml` for libraries unique to that service.

After modifying a `pyproject.toml` file, the corresponding Docker image must be rebuilt. For example:
```bash
docker compose build receiver