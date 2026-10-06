#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly COLLECTOR_VERSION="1"
readonly LGTM_CONTAINER="taskflow-m4-otel-lgtm"
readonly OUTPUT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/incidents"

usage() {
    cat >&2 <<'USAGE'
Usage:
  collect-evidence.sh <incident-id> <release-sha> <start-rfc3339> <end-rfc3339> <alert-state>

Arguments:
  incident-id    Stable incident identifier.
  release-sha    Exact 40-character deployed release SHA.
  start-rfc3339  Evidence window start, e.g. 2026-10-05T10:14:00Z.
  end-rfc3339    Evidence window end, e.g. 2026-10-05T10:16:00Z.
  alert-state    Observed alert state: firing | normal | no_data | error.

The collector is fixed to:
  operation       = tasks.list
  environment     = dev
  alert UID       = taskflow-p4-tasks-list-failure
  telemetry host  = taskflow-m4-otel-lgtm
  recovery target = M4 DEV only

No arbitrary commands or telemetry queries are accepted.
USAGE
    exit 2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ "$#" -eq 5 ]] || usage

readonly INCIDENT_ID="$1"
readonly RELEASE_SHA="$(printf "%s" "$2" | tr "[:upper:]" "[:lower:]")"
readonly START_RFC3339="$3"
readonly END_RFC3339="$4"
readonly ALERT_STATE="$5"

[[ "$INCIDENT_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$ ]] \
    || fail "invalid incident ID"

[[ "$RELEASE_SHA" =~ ^[0-9a-fA-F]{40}$ ]] \
    || fail "release SHA must be exactly 40 hexadecimal characters"

case "$ALERT_STATE" in
    firing|normal|no_data|error) ;;
    *) fail "invalid alert state: expected firing|normal|no_data|error" ;;
esac

for command in curl docker date python3; do
    command -v "$command" >/dev/null 2>&1 \
        || fail "required command not found: $command"
done

docker inspect "$LGTM_CONTAINER" >/dev/null 2>&1 \
    || fail "required observability container not found: $LGTM_CONTAINER"

parse_epoch() {
    date -u -d "$1" +%s 2>/dev/null \
        || fail "invalid RFC3339 timestamp: $1"
}

readonly START_EPOCH="$(parse_epoch "$START_RFC3339")"
readonly END_EPOCH="$(parse_epoch "$END_RFC3339")"
readonly NOW_EPOCH="$(date -u +%s)"

(( END_EPOCH > START_EPOCH )) \
    || fail "end timestamp must be after start timestamp"

readonly WINDOW_SECONDS="$((END_EPOCH - START_EPOCH))"

(( WINDOW_SECONDS <= 600 )) \
    || fail "evidence window must not exceed 10 minutes"

(( END_EPOCH <= NOW_EPOCH + 60 )) \
    || fail "end timestamp is too far in the future"

readonly START_NS="$((START_EPOCH * 1000000000))"
readonly END_NS="$((END_EPOCH * 1000000000))"

readonly OUT_DIR="${OUTPUT_ROOT}/${INCIDENT_ID}"
readonly OUT_FILE="${OUT_DIR}/evidence.json"
readonly LOCK_DIR="${OUT_DIR}/.collect.lock"
readonly TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_DIR"
    rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$OUT_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    fail "evidence collection already running for incident: $INCIDENT_ID"
fi

run_lgtm_curl() {
    docker exec "$LGTM_CONTAINER" curl -sS --max-time 5 "$@"
}

run_lgtm_curl_optional() {
    local output_path="$1"
    shift

    if ! run_lgtm_curl "$@" >"$output_path" 2>"$TMP_DIR/telemetry.stderr"; then
        printf '%s\n' '{"status":"unavailable","error":"telemetry_request_failed"}' >"$output_path"
        return 0
    fi

    if [[ ! -s "$output_path" ]] || ! python3 -m json.tool "$output_path" >/dev/null 2>&1; then
        printf '%s\n' '{"status":"unavailable","error":"telemetry_response_invalid"}' >"$output_path"
    fi
}

echo "Collecting bounded TaskFlow evidence..."
echo "Incident: $INCIDENT_ID"
echo "Release:  $RELEASE_SHA"
echo "Window:   $START_RFC3339 → $END_RFC3339"
echo "Alert:    $ALERT_STATE"

# ---------------------------------------------------------------------------
# 1. Historical application behavior from Tempo: HTTP 503 on /api/tasks.
#    Never probe the live application; collection must not create an incident.
# ---------------------------------------------------------------------------
application_tempo_query='{ resource.service.name = "taskflow-backend" && resource."deployment.environment.name" = "dev" && resource."service.version" = "'"$RELEASE_SHA"'" && span:name = "GET /api/tasks" && span."http.status_code" = 503 && span."http.host" != "testserver" }'

run_lgtm_curl_optional "$TMP_DIR/application.json" \
    -G \
    "http://127.0.0.1:3200/api/search" \
    --data-urlencode "q=${application_tempo_query}" \
    --data-urlencode "start=${START_EPOCH}" \
    --data-urlencode "end=${END_EPOCH}" \
    --data-urlencode "limit=20"

# ---------------------------------------------------------------------------
# 2. Prometheus: fixed queries only.
# ---------------------------------------------------------------------------
prom_requests_query='sum by (outcome) (rate(taskflow_api_tasks_list_requests_total{service_name="taskflow-backend",deployment_environment_name="dev",service_version="'"$RELEASE_SHA"'",operation="tasks.list"}[1m]))'
prom_errors_query='sum(rate(taskflow_api_tasks_list_errors_total{service_name="taskflow-backend",deployment_environment_name="dev",service_version="'"$RELEASE_SHA"'",operation="tasks.list"}[1m]))'

run_lgtm_curl_optional "$TMP_DIR/prom_requests.json" \
    -G \
    "http://127.0.0.1:9090/api/v1/query_range" \
    --data-urlencode "query=${prom_requests_query}" \
    --data-urlencode "start=${START_EPOCH}" \
    --data-urlencode "end=${END_EPOCH}" \
    --data-urlencode "step=60s" \
    --data-urlencode "limit=20"

run_lgtm_curl_optional "$TMP_DIR/prom_errors.json" \
    -G \
    "http://127.0.0.1:9090/api/v1/query_range" \
    --data-urlencode "query=${prom_errors_query}" \
    --data-urlencode "start=${START_EPOCH}" \
    --data-urlencode "end=${END_EPOCH}" \
    --data-urlencode "step=60s" \
    --data-urlencode "limit=20"

# ---------------------------------------------------------------------------
# 3. Loki: same bounded failure signal used by the P4 alert.
# ---------------------------------------------------------------------------
loki_query='{service_name="taskflow-backend",deployment_environment_name="dev"} | service_version="'"$RELEASE_SHA"'" |= "Task list failed" | operation="tasks.list" | outcome="error" | keep operation,taskflow_environment,taskflow_release,outcome,error_type,otelTraceID,otelSpanID'

run_lgtm_curl_optional "$TMP_DIR/loki.json" \
    -G \
    "http://127.0.0.1:3100/loki/api/v1/query_range" \
    --data-urlencode "query=${loki_query}" \
    --data-urlencode "start=${START_NS}" \
    --data-urlencode "end=${END_NS}" \
    --data-urlencode "limit=20" \
    --data-urlencode "direction=backward"

# ---------------------------------------------------------------------------
# 4. Tempo: fixed TraceQL search for tasks.list in the same DEV release.
#    Return metadata only; do not fetch full traces.
# ---------------------------------------------------------------------------
tempo_query='{ resource.service.name = "taskflow-backend" && span:name = "tasks.list" && span."taskflow.environment" = "dev" && span."taskflow.release" = "'"$RELEASE_SHA"'" }'

run_lgtm_curl_optional "$TMP_DIR/tempo.json" \
    -G \
    "http://127.0.0.1:3200/api/search" \
    --data-urlencode "q=${tempo_query}" \
    --data-urlencode "start=${START_EPOCH}" \
    --data-urlencode "end=${END_EPOCH}" \
    --data-urlencode "limit=20"

# ---------------------------------------------------------------------------
# 5. Build a minimized, redacted evidence packet.
# ---------------------------------------------------------------------------
python3 - \
    "$TMP_DIR/application.json" \
    "$TMP_DIR/prom_requests.json" \
    "$TMP_DIR/prom_errors.json" \
    "$TMP_DIR/loki.json" \
    "$TMP_DIR/tempo.json" \
    "$OUT_FILE" \
    "$INCIDENT_ID" \
    "$RELEASE_SHA" \
    "$START_RFC3339" \
    "$END_RFC3339" \
    "$WINDOW_SECONDS" \
    "$ALERT_STATE" \
    "$COLLECTOR_VERSION" <<'PY'
import json
import re
import sys
from pathlib import Path

(
    application_path,
    prom_requests_path,
    prom_errors_path,
    loki_path,
    tempo_path,
    output_path,
    incident_id,
    release_sha,
    start_rfc3339,
    end_rfc3339,
    window_seconds,
    alert_state,
    collector_version,
) = sys.argv[1:]

SENSITIVE = re.compile(
    r'(?i)(password|passwd|token|api[_-]?key|authorization|secret|database_url)'
    r'(\s*[=:]\s*)("[^"]*"|[^,\s}]+)'
)
BEARER = re.compile(r'(?i)(Bearer\s+)[A-Za-z0-9._~+/\-=]+')

def redact(value):
    if isinstance(value, str):
        value = SENSITIVE.sub(r'\1\2[REDACTED]', value)
        value = BEARER.sub(r'\1[REDACTED]', value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(val) for key, val in value.items()}
    return value

def load_json(path):
    try:
        return redact(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {"status": "unavailable"}

def minimize_prometheus(payload):
    if not isinstance(payload, dict):
        return {"status": "invalid"}
    if payload.get("status") == "unavailable":
        return {
            "status": "unavailable",
            "error": payload.get("error", "telemetry_unavailable"),
        }
    return {
        "status": payload.get("status"),
        "warnings": payload.get("warnings", []),
        "data": {
            "resultType": payload.get("data", {}).get("resultType"),
            "result": payload.get("data", {}).get("result", []),
        },
    }

def minimize_loki(payload):
    if not isinstance(payload, dict):
        return {"status": "invalid"}
    if payload.get("status") == "unavailable":
        return {
            "status": "unavailable",
            "error": payload.get("error", "telemetry_unavailable"),
        }
    results = []
    for stream in payload.get("data", {}).get("result", [])[:20]:
        results.append({
            "stream": stream.get("stream", {}),
            "values": stream.get("values", [])[:20],
        })
    return {
        "status": payload.get("status"),
        "data": {
            "resultType": payload.get("data", {}).get("resultType"),
            "result": results,
        },
    }

def minimize_application(payload):
    if not isinstance(payload, dict):
        return {"status": "invalid", "source": "tempo"}
    if payload.get("status") == "unavailable":
        return {
            "status": "unavailable",
            "source": "tempo",
            "error": payload.get("error", "telemetry_unavailable"),
        }

    matches = []
    for trace in payload.get("traces", [])[:20]:
        groups = []
        span_set = trace.get("spanSet")
        if isinstance(span_set, dict):
            groups.append(span_set)
        for group in trace.get("spanSets", [])[:20]:
            if isinstance(group, dict):
                groups.append(group)

        for group in groups:
            for span in group.get("spans", [])[:20]:
                attrs = {}
                for attr in span.get("attributes", []):
                    key = attr.get("key")
                    value = attr.get("value", {})
                    if not key or not isinstance(value, dict):
                        continue
                    if "stringValue" in value:
                        attrs[key] = value["stringValue"]
                    elif "intValue" in value:
                        attrs[key] = value["intValue"]
                    elif "boolValue" in value:
                        attrs[key] = value["boolValue"]

                if str(attrs.get("http.status_code")) != "503":
                    continue
                if attrs.get("http.host") == "testserver":
                    continue

                matches.append({
                    "traceID": trace.get("traceID"),
                    "spanID": span.get("spanID"),
                    "status_code": 503,
                    "host": attrs.get("http.host"),
                    "route": attrs.get("http.route"),
                    "target": attrs.get("http.target"),
                    "method": attrs.get("http.method"),
                    "url": attrs.get("http.url"),
                    "startTimeUnixNano": span.get("startTimeUnixNano"),
                    "durationNanos": span.get("durationNanos"),
                })

    return {
        "status": payload.get("status", "success"),
        "source": "tempo",
        "matches": matches[:20],
        "match_count": len(matches[:20]),
    }

def minimize_tempo(payload):
    if not isinstance(payload, dict):
        return {"status": "invalid"}
    if payload.get("status") == "unavailable":
        return {
            "status": "unavailable",
            "error": payload.get("error", "telemetry_unavailable"),
        }

    traces = []
    for trace in payload.get("traces", [])[:20]:
        traces.append({
            "traceID": trace.get("traceID"),
            "rootServiceName": trace.get("rootServiceName"),
            "rootTraceName": trace.get("rootTraceName"),
            "startTimeUnixNano": trace.get("startTimeUnixNano"),
            "durationMs": trace.get("durationMs"),
        })

    result = {
        "traces": traces,
    }
    if "metrics" in payload:
        result["metrics"] = payload["metrics"]
    return result

artifact_relative_path = f"module-4/incident-response/incidents/{incident_id}/evidence.json"

packet = {
    "artifact": {
        "kind": "repo-evidence",
        "path": artifact_relative_path,
        "retention": "repository-controlled",
    },
    "collector": {
        "version": collector_version,
        "mode": "bounded-read-only",
    },
    "incident": {
        "incident_id": incident_id,
        "operation": "tasks.list",
        "environment": "dev",
        "release_sha": release_sha,
        "evidence_window": {
            "start": start_rfc3339,
            "end": end_rfc3339,
            "max_window_seconds": 600,
            "window_seconds": int(window_seconds),
        },
    },
    "alert": {
        "uid": "taskflow-p4-tasks-list-failure",
        "title": "TaskFlow /api/tasks user-impact failure",
        "state": alert_state,
        "state_source": "external-alert-context",
        "labels": {
            "operation": "tasks.list",
            "severity": "critical",
            "user_impact": "true",
        },
    },
    "application": minimize_application(load_json(application_path)),
    "metrics": {
        "requests_rate": minimize_prometheus(load_json(prom_requests_path)),
        "errors_rate": minimize_prometheus(load_json(prom_errors_path)),
    },
    "logs": minimize_loki(load_json(loki_path)),
    "traces": minimize_tempo(load_json(tempo_path)),
    "safety": {
        "arbitrary_commands": False,
        "arbitrary_queries": False,
        "production_access": False,
        "secrets_included": False,
        "full_application_response_retained": False,
        "full_trace_payload_retained": False,
    },
}

def prometheus_has_nonzero_value(payload):
    for series in payload.get("data", {}).get("result", []):
        for sample in series.get("values", []):
            try:
                if float(sample[1]) != 0:
                    return True
            except (IndexError, TypeError, ValueError):
                continue
    return False

application_trace_ids = {
    match.get("traceID")
    for match in packet["application"].get("matches", [])
    if match.get("traceID")
}
tasks_trace_ids = {
    trace.get("traceID")
    for trace in packet["traces"].get("traces", [])
    if trace.get("traceID")
}

failure_log_streams = packet["logs"].get("data", {}).get("result", [])
correlated_log = False
for stream in failure_log_streams:
    trace_id = stream.get("stream", {}).get("otelTraceID")
    if trace_id and trace_id in application_trace_ids:
        correlated_log = True
        break

source_statuses = {
    "application": packet["application"].get("status") not in {None, "unavailable", "invalid"},
    "prom_requests": packet["metrics"]["requests_rate"].get("status") == "success",
    "prom_errors": packet["metrics"]["errors_rate"].get("status") == "success",
    "loki": packet["logs"].get("status") == "success",
    "tempo": packet["traces"].get("status", "success") == "success",
}
packet["collection"] = {
    "partial": not all(source_statuses.values()),
    "source_statuses": source_statuses,
    "evidence_found": {
        "application_503": packet["application"].get("match_count", 0) > 0,
        "error_metrics": prometheus_has_nonzero_value(packet["metrics"]["errors_rate"]),
        "failure_logs": bool(failure_log_streams),
        "correlated_failure_log": correlated_log,
        "tasks_list_traces": bool(tasks_trace_ids),
        "correlated_incident_trace": bool(application_trace_ids & tasks_trace_ids),
    },
}

Path(output_path).write_text(
    json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
PY

chmod 600 "$OUT_FILE"

# Final sanity check: valid JSON and expected fixed scope.
python3 - "$OUT_FILE" <<'PY'
import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))

assert packet["incident"]["operation"] == "tasks.list"
assert packet["incident"]["environment"] == "dev"
assert packet["alert"]["uid"] == "taskflow-p4-tasks-list-failure"
assert packet["application"].get("source") == "tempo"
assert packet["safety"]["arbitrary_commands"] is False
assert packet["safety"]["arbitrary_queries"] is False
assert packet["safety"]["production_access"] is False
assert packet["safety"]["secrets_included"] is False

print(f"Evidence packet: {sys.argv[1]}")
print("Evidence packet validation: PASS")
PY

echo "Evidence collection complete."
