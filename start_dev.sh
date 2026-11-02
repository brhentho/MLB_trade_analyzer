#!/bin/bash
# Start the API (8000) and web app (3000) for local development.
set -e
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
$PY backend/main.py &
API_PID=$!
(cd frontend && npm run dev) &
WEB_PID=$!
trap 'kill $API_PID $WEB_PID 2>/dev/null' INT TERM EXIT
echo "API: http://localhost:8000   Web: http://localhost:3000"
wait