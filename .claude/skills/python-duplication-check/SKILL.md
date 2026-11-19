---
name: python-duplication-check
description: "Rules for checking code duplication (copy-paste) in Python files. Use this after modifying or refactoring logic to ensure codebase health."
---

# Python Code Duplication Check

This project uses `pylint` (specifically its similarity checker) to identify redundant code blocks.

## 1. When to Run
- **MANDATORY**: Run after every significant change to Python logic (`apps/`).
- **ESPECIALLY IMPORTANT**: When refactoring services, creating new management commands, or duplicating logic.
- This helps identify opportunities for abstraction (e.g., moving shared logic to a base class or utility).

## 2. Command Reference
The duplication check runs inside Docker via the Makefile:

- **Check for duplicates**: `make check-dupes`

## 3. Configuration
The configuration is stored in `pyproject.toml` under `[tool.pylint.similarities]`.
- **Threshold**: Currently set to 4 lines. Any block identical across 8+ lines will be flagged.
- **Exclusions**: The check automatically ignores `migrations/` to avoid flagging Django's boilerplate.
- **Ignore List**: The checker is configured to ignore comments, docstrings, imports, and function signatures to focus purely on logic.
