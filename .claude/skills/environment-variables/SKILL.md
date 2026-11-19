---
name: environment-variables
description: "Use when reading, writing, or referencing environment variables, .env files, config keys, secrets, base URLs, or any system-level configuration in Python projects."
---

# Environment Variables

## Storage & Management

Variables live in `.env` (which is **strictly inaccessible to you**). You must never attempt to read, write, or even `grep` the `.env` file, as it contains sensitive user secrets. Use `.env.dist` as your only reference for environment variable availability.

- **Only** add, edit, or delete variables in `.env.dist`.
- **CRITICAL RULE:** Do not use `grep`, `cat`, or any terminal command on `.env`. If you need to know what variables exist, look at `.env.dist`.
- If you make changes to `.env.dist` or add new environment variable usage in the code, you **MUST** immediately instruct the user to update their `.env` file manually.

## Naming Convention

Use `SCREAMING_SNAKE_CASE`. Prefix with the service or domain when relevant:
```
STRIPE_SECRET_KEY=sk_test_...
DATABASE_URL=postgres://user:pass@localhost:5432/db
APP_DEBUG=true
```

## Rules

- **Never hardcode** secrets, keys, URLs, or config values in source code
- All base URLs, API keys, hashes, passwords, and system config must be in `.env.dist`

## Usage
```python
import os

# Optional variable with a fallback default
external_api_base_url = os.environ.get("PROVIDER_API_BASE_URL", "https://api.default.com")

# Required variable — raises KeyError if missing (preferred for critical vars)
stripe_gateway_secret_key = os.environ["STRIPE_SECRET_KEY"]
```

Use `os.environ["VAR_NAME"]` for variables the app cannot function without. Use `os.environ.get()` only when a default is genuinely safe. Always use descriptive names for variables capturing environment values.
