#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-}"
PASSWORD="${PASSWORD:-}"

if [[ -z "${EMAIL}" || -z "${PASSWORD}" ]]; then
  echo "Usage:"
  echo "  EMAIL='your@email' PASSWORD='your_password' [BASE_URL='http://127.0.0.1:8000'] $0"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (brew install jq)"
  exit 1
fi

echo "Logging in against ${BASE_URL} ..."
TOKEN="$(
  curl -sS -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" \
    | jq -r '.access_token'
)"

if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then
  echo "Login failed. Check EMAIL/PASSWORD and backend logs."
  exit 1
fi

AUTH_HEADER="Authorization: Bearer ${TOKEN}"
echo "Token received."

echo
echo "1) /api/auth/me"
curl -sS "${BASE_URL}/api/auth/me" -H "${AUTH_HEADER}" | jq

echo
echo "2) /api/products (list)"
curl -sS "${BASE_URL}/api/products" -H "${AUTH_HEADER}" | jq

echo
echo "3) /api/scrape (public url scrape example)"
curl -sS -X POST "${BASE_URL}/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.cyberport.de/"}' | jq

echo
echo "Done. You can now manually test with the same token in Swagger Authorize."
