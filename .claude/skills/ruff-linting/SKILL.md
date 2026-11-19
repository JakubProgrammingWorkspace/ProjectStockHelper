---
name: ruff-linting
description: "Rules for running ruff linting and formatting on backend Python code. Essential for maintaining code quality and consistent style."
---

# Ruff Linting & Formatting

This project uses `ruff` for fast linting and formatting of the Django backend code.

## 1. When to Run
- **MANDATORY**: Run linting and formatting after every modification to backend Python files (`apps/`, `config/`, `manage.py`, etc.).
- Before submitting any change, ensure the code is clean.

## 2. Command Reference
All commands must be run via the Makefile as the application runs in Docker:

- **Check for issues**: `make lint`
- **Fix issues automatically**: `make lint-fix`
- **Format code**: `make format`

## 3. Configuration
Configuration resides in `pyproject.toml` under `[tool.ruff]`.
Special rules:
- Line length is set to 120.
- Migrations are entirely excluded from all ruff checks.
- Star imports (`F403`, `F405`) are ignored in Django settings files (`**/settings/*.py`) to accommodate the project's base/dev/prod settings structure.
