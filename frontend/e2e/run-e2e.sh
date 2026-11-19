#!/usr/bin/env bash
# Wait until the Vite dev server (started by the `frontend` container, which also
# installs node_modules) answers, then run the Playwright suite.
# Running `npm install` here as well would race with the frontend container.
set -euo pipefail
cd "$(dirname "$0")/.."

frontend_url="http://frontend:3000"
for _ in $(seq 1 90); do
  if node -e "fetch('${frontend_url}').then(() => process.exit(0), () => process.exit(1))"; then
    exec npx playwright test
  fi
  sleep 2
done

echo "Frontend did not become ready at ${frontend_url} within 180s" >&2
exit 1
