#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly VERIFIER_VERSION="1"
readonly DEV_API_URL="https://dev-api.zctaskflow.athing.cc/api/tasks"
readonly OUTPUT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/incidents"
readonly MAX_RESPONSE_BYTES=1048576
readonly CONNECT_TIMEOUT_SECONDS=5
readonly MAX_TIME_SECONDS=15

usage() {
    cat >&2 <<'USAGE'
Usage:
  verify-recovery.sh <incident-id>

Purpose:
  Independently verify recovery of the TaskFlow P4 user-impacting
  GET /api/tasks condition.

The verifier is read-only and fixed to the TaskFlow DEV endpoint.
It does not execute Docker, AWS, SSM, deployment, rollback, or mutation commands.

Allowed outcomes:
  verified
  unresolved
  inconclusive
USAGE
    exit 2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ "$#" -eq 1 ]] || usage

readonly INCIDENT_ID="$1"

[[ "$INCIDENT_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$ ]] \
    || fail "invalid incident ID"

command -v curl >/dev/null 2>&1 \
    || fail "required command not found: curl"

command -v python3 >/dev/null 2>&1 \
    || fail "required command not found: python3"

readonly INCIDENT_DIR="$OUTPUT_ROOT/$INCIDENT_ID"
readonly VERIFICATION_FILE="$INCIDENT_DIR/recovery-verification.json"
readonly TMP_DIR="$(mktemp -d)"
readonly BODY_FILE="$TMP_DIR/response.body"
readonly HEADERS_FILE="$TMP_DIR/response.headers"

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT

mkdir -p "$INCIDENT_DIR"

RESULT=""
REASON=""
HTTP_STATUS=""
CURL_RC=0
RESPONSE_BYTES=0
JSON_ARRAY=false

set +e
HTTP_STATUS="$(
    curl \
        --silent \
        --show-error \
        --connect-timeout "$CONNECT_TIMEOUT_SECONDS" \
        --max-time "$MAX_TIME_SECONDS" \
        --proto '=https' \
        --tlsv1.2 \
        --dump-header "$HEADERS_FILE" \
        --output "$BODY_FILE" \
        --write-out '%{http_code}' \
        "$DEV_API_URL"
)"
CURL_RC=$?
set -e

if (( CURL_RC != 0 )); then
    RESULT="inconclusive"
    REASON="verification request failed before a trustworthy HTTP response was obtained"
elif [[ ! "$HTTP_STATUS" =~ ^[0-9]{3}$ ]]; then
    RESULT="inconclusive"
    REASON="verification returned an invalid HTTP status"
else
    RESPONSE_BYTES="$(wc -c <"$BODY_FILE")"

    if (( RESPONSE_BYTES > MAX_RESPONSE_BYTES )); then
        RESULT="inconclusive"
        REASON="verification response exceeded the bounded response size"
    elif [[ "$HTTP_STATUS" != "200" ]]; then
        RESULT="unresolved"
        REASON="GET /api/tasks did not return HTTP 200"
    else
        if python3 - "$BODY_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "rb") as fh:
    payload = json.load(fh)

if not isinstance(payload, list):
    raise SystemExit(1)
PY
        then
            JSON_ARRAY=true
            RESULT="verified"
            REASON="GET /api/tasks returned HTTP 200 with a valid JSON array"
        else
            RESULT="unresolved"
            REASON="GET /api/tasks returned HTTP 200 but the response was not a valid JSON array"
        fi
    fi
fi

CHECKED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - \
    "$VERIFIER_VERSION" \
    "$INCIDENT_ID" \
    "$CHECKED_AT" \
    "$DEV_API_URL" \
    "$RESULT" \
    "$REASON" \
    "$HTTP_STATUS" \
    "$RESPONSE_BYTES" \
    "$JSON_ARRAY" \
    >"$VERIFICATION_FILE" <<'PY'
import json
import sys

(
    verifier_version,
    incident_id,
    checked_at,
    endpoint,
    result,
    reason,
    http_status,
    response_bytes,
    json_array,
) = sys.argv[1:]

record = {
    "verifier_version": verifier_version,
    "incident_id": incident_id,
    "checked_at": checked_at,
    "endpoint": endpoint,
    "operation": "tasks.list",
    "environment": "dev",
    "result": result,
    "reason": reason,
    "http_status": http_status or None,
    "response_bytes": int(response_bytes),
    "json_array": json_array == "true",
    "mutation_performed": False,
}

print(json.dumps(record, indent=2))
PY

echo "VERIFICATION_RESULT=$RESULT"
echo "INCIDENT_ID=$INCIDENT_ID"
echo "HTTP_STATUS=${HTTP_STATUS:-none}"
echo "VERIFICATION_FILE=$VERIFICATION_FILE"
echo "REASON=$REASON"
