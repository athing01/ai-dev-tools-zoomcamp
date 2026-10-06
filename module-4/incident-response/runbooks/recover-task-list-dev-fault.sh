#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly ACTION_ID="recover_task_list_dev_fault"
readonly ALERT_UID="taskflow-p4-tasks-list-failure"
readonly OPERATION="tasks.list"
readonly ENVIRONMENT="dev"
readonly RUNTIME_DIR="/opt/taskflow-m4-dev"
readonly COMPOSE_PROJECT="taskflow-m4-dev"
readonly COMPOSE_FILE="/opt/taskflow-m4-dev/docker-compose.ec2.yml"
readonly SERVICE="backend"
readonly AUTH_MAX_AGE_SECONDS=600

usage() {
    cat >&2 <<'USAGE'
Usage:
  recover-task-list-dev-fault.sh <authorization-json>

Purpose:
  Execute the single allowlisted TaskFlow P5 recovery action:
  recover_task_list_dev_fault

Arguments:
  authorization-json  Human authorization record. No executable commands.
USAGE
    exit 2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ "$#" -eq 1 ]] || usage

readonly AUTH_FILE="$1"
readonly EXECUTION_TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

[[ -f "$AUTH_FILE" ]] \
    || fail "authorization file not found: $AUTH_FILE"

[[ ! -L "$AUTH_FILE" ]] \
    || fail "authorization file must not be a symbolic link"

# Fixed action scope. These values are implementation constants, not
# model-controlled inputs. They must match the allowlisted policy action.
[[ "$ACTION_ID" == "recover_task_list_dev_fault" ]] \
    || fail "action scope mismatch"

[[ "$ALERT_UID" == "taskflow-p4-tasks-list-failure" ]] \
    || fail "alert scope mismatch"

[[ "$OPERATION" == "tasks.list" ]] \
    || fail "operation scope mismatch"

[[ "$ENVIRONMENT" == "dev" ]] \
    || fail "environment scope mismatch"

[[ "$SERVICE" == "backend" ]] \
    || fail "service scope mismatch"

for command in date python3; do
    command -v "$command" >/dev/null 2>&1 \
        || fail "required command not found: $command"
done

get_container_env() {
    local container_id="$1"
    local key="$2"

    docker inspect "$container_id" \
        --format '{{range .Config.Env}}{{println .}}{{end}}' |
        awk -v key="$key" '
            index($0, key "=") == 1 {
                print substr($0, length(key) + 2)
                found = 1
                exit 0
            }
            END {
                if (!found) {
                    exit 1
                }
            }
        '
}

readonly TMP_DIR="$(mktemp -d)"

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT

readonly AUTH_META="$TMP_DIR/authorization.tsv"

python3 - "$AUTH_FILE" "$EXECUTION_TIMESTAMP" "$AUTH_MAX_AGE_SECONDS" >"$AUTH_META" <<'PY'
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
execution_timestamp_raw = sys.argv[2]
max_age_seconds = int(sys.argv[3])

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"invalid authorization JSON: {exc}")

if not isinstance(data, dict):
    raise SystemExit("authorization record must be a JSON object")

required = {
    "authorization_id",
    "decision",
    "incident_id",
    "action_id",
    "alert_uid",
    "operation",
    "environment",
    "approver",
    "authorized_at",
}

if set(data) != required:
    raise SystemExit("authorization record fields do not exactly match the fixed contract")

patterns = {
    "authorization_id": r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    "incident_id": r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$",
    "approver": r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$",
}

for field, pattern in patterns.items():
    value = data.get(field)
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise SystemExit(f"invalid authorization field: {field}")

if data["decision"] != "approved":
    raise SystemExit("authorization decision is not approved")
if data["action_id"] != "recover_task_list_dev_fault":
    raise SystemExit("authorization action_id is not allowlisted")
if data["alert_uid"] != "taskflow-p4-tasks-list-failure":
    raise SystemExit("authorization alert_uid mismatch")
if data["operation"] != "tasks.list":
    raise SystemExit("authorization operation mismatch")
if data["environment"] != "dev":
    raise SystemExit("authorization environment mismatch")

try:
    timestamp = datetime.fromisoformat(data["authorized_at"].replace("Z", "+00:00"))
except ValueError as exc:
    raise SystemExit(f"invalid authorized_at: {exc}")

if timestamp.tzinfo is None:
    raise SystemExit("authorized_at must include timezone")

try:
    execution_timestamp = datetime.fromisoformat(
        execution_timestamp_raw.replace("Z", "+00:00")
    )
except ValueError as exc:
    raise SystemExit(f"invalid execution timestamp: {exc}")

if execution_timestamp.tzinfo is None:
    raise SystemExit("execution timestamp must include timezone")

if timestamp > execution_timestamp:
    raise SystemExit("authorization is from the future")

if (execution_timestamp - timestamp).total_seconds() > max_age_seconds:
    raise SystemExit("authorization has expired")

print("\t".join([
    data["authorization_id"],
    data["decision"],
    data["incident_id"],
    data["action_id"],
    data["alert_uid"],
    data["operation"],
    data["environment"],
    data["approver"],
    data["authorized_at"],
]))
PY

IFS=$'\t' read -r \
    AUTHORIZATION_ID \
    AUTHORIZATION_DECISION \
    AUTH_INCIDENT_ID \
    AUTH_ACTION_ID \
    AUTH_ALERT_UID \
    AUTH_OPERATION \
    AUTH_ENVIRONMENT \
    AUTH_APPROVER \
    AUTH_AUTHORIZED_AT <"$AUTH_META"

readonly AUTHORIZATION_ID
readonly AUTHORIZATION_DECISION
readonly INCIDENT_ID="$AUTH_INCIDENT_ID"
readonly AUTHORIZED_ACTION_ID="$AUTH_ACTION_ID"
readonly AUTHORIZED_ALERT_UID="$AUTH_ALERT_UID"
readonly AUTHORIZED_OPERATION="$AUTH_OPERATION"
readonly AUTHORIZED_ENVIRONMENT="$AUTH_ENVIRONMENT"
readonly APPROVER="$AUTH_APPROVER"
readonly AUTH_AUTHORIZED_AT

[[ "$AUTHORIZED_ACTION_ID" == "$ACTION_ID" ]] \
    || fail "authorization action does not match executor action"
[[ "$AUTHORIZED_ALERT_UID" == "$ALERT_UID" ]] \
    || fail "authorization alert UID does not match executor scope"
[[ "$AUTHORIZED_OPERATION" == "$OPERATION" ]] \
    || fail "authorization operation does not match executor scope"
[[ "$AUTHORIZED_ENVIRONMENT" == "$ENVIRONMENT" ]] \
    || fail "authorization environment does not match executor scope"

for command in docker sha256sum; do
    command -v "$command" >/dev/null 2>&1 \
        || fail "required command not found: $command"
done

docker compose version >/dev/null 2>&1 \
    || fail "docker compose is not available"

readonly PRE_ENV_FILE="$TMP_DIR/backend-env-before.txt"
readonly POST_ENV_FILE="$TMP_DIR/backend-env-after.txt"

RESULT="not_executed"

PRE_BACKEND_ID=""
POST_BACKEND_ID=""
PRE_FRONTEND_ID=""
POST_FRONTEND_ID=""
PRE_CADDY_ID=""
POST_CADDY_ID=""
PRE_IMAGE_ID=""
POST_IMAGE_ID=""
PRE_IMAGE_REF=""
POST_IMAGE_REF=""
PRE_FAULT_MODE=""
POST_FAULT_MODE=""
PRE_RUNTIME_ENV_SHA=""
POST_RUNTIME_ENV_SHA=""

[[ -d "$RUNTIME_DIR" ]] \
    || fail "runtime directory missing: $RUNTIME_DIR"

cd "$RUNTIME_DIR"

[[ -f "$COMPOSE_FILE" ]] \
    || fail "compose file missing: $COMPOSE_FILE"

[[ -f "$RUNTIME_DIR/runtime.env" ]] \
    || fail "runtime.env missing"

# ---------------------------------------------------------------------------
# 1. Immediate precondition revalidation.
# ---------------------------------------------------------------------------

docker compose \
    --env-file runtime.env \
    -f "$COMPOSE_FILE" \
    config --services |
    grep -Fx "$SERVICE" >/dev/null \
    || fail "backend service is not present in compose configuration"

PRE_BACKEND_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q backend
)"

PRE_FRONTEND_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q frontend
)"

PRE_CADDY_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q caddy
)"

[[ -n "$PRE_BACKEND_ID" ]] || fail "backend container not found"
[[ -n "$PRE_FRONTEND_ID" ]] || fail "frontend container not found"
[[ -n "$PRE_CADDY_ID" ]] || fail "caddy container not found"

PRE_PROJECT="$(
    docker inspect "$PRE_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project"}}'
)"

PRE_WORKDIR="$(
    docker inspect "$PRE_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
)"

PRE_CONFIG_FILES="$(
    docker inspect "$PRE_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'
)"

PRE_ENVIRONMENT="$(get_container_env "$PRE_BACKEND_ID" TASKFLOW_ENVIRONMENT)" \
    || fail "TASKFLOW_ENVIRONMENT is missing"

PRE_FAULT_MODE="$(get_container_env "$PRE_BACKEND_ID" TASKFLOW_P4_FAULT_MODE)" \
    || fail "TASKFLOW_P4_FAULT_MODE is missing"

PRE_IMAGE_ID="$(
    docker inspect "$PRE_BACKEND_ID" \
        --format '{{.Image}}'
)"

PRE_IMAGE_REF="$(
    docker inspect "$PRE_BACKEND_ID" \
        --format '{{.Config.Image}}'
)"

PRE_RUNTIME_ENV_SHA="$(
    sha256sum "$RUNTIME_DIR/runtime.env" |
        cut -d' ' -f1
)"

docker inspect "$PRE_BACKEND_ID" \
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    sed '/^TASKFLOW_P4_FAULT_MODE=/d' |
    sort >"$PRE_ENV_FILE"

[[ "$PRE_PROJECT" == "$COMPOSE_PROJECT" ]] \
    || fail "compose project mismatch"

[[ "$PRE_WORKDIR" == "$RUNTIME_DIR" ]] \
    || fail "compose working directory mismatch"

[[ "$PRE_CONFIG_FILES" == "$COMPOSE_FILE" ]] \
    || fail "compose configuration mismatch"

[[ "$PRE_ENVIRONMENT" == "$ENVIRONMENT" ]] \
    || fail "environment is not dev"

[[ "$PRE_FAULT_MODE" == "list_fail" ]] \
    || fail "TASKFLOW_P4_FAULT_MODE is not list_fail"

[[ "$PRE_BACKEND_ID" != "$PRE_FRONTEND_ID" ]] \
    || fail "backend/frontend container identity collision"

[[ "$PRE_BACKEND_ID" != "$PRE_CADDY_ID" ]] \
    || fail "backend/caddy container identity collision"

echo "ACTION_ID=$ACTION_ID"
echo "INCIDENT_ID=$INCIDENT_ID"
echo "AUTHORIZATION_ID=$AUTHORIZATION_ID"
echo "AUTHORIZATION_DECISION=$AUTHORIZATION_DECISION"
echo "APPROVER=$APPROVER"
echo "AUTHORIZATION_TIMESTAMP=$AUTH_AUTHORIZED_AT"
echo "EXECUTION_TIMESTAMP=$EXECUTION_TIMESTAMP"
echo "PRECONDITIONS=PASS"
echo "PRE_PROJECT=$PRE_PROJECT"
echo "PRE_WORKDIR=$PRE_WORKDIR"
echo "PRE_CONFIG_FILES=$PRE_CONFIG_FILES"
echo "PRE_ENVIRONMENT=$PRE_ENVIRONMENT"
echo "PRE_FAULT_MODE=$PRE_FAULT_MODE"
echo "PRE_BACKEND_ID=$PRE_BACKEND_ID"
echo "PRE_FRONTEND_ID=$PRE_FRONTEND_ID"
echo "PRE_CADDY_ID=$PRE_CADDY_ID"
echo "PRE_IMAGE_REF=$PRE_IMAGE_REF"

# ---------------------------------------------------------------------------
# 2. Fixed bounded mutation.
# ---------------------------------------------------------------------------

TASKFLOW_P4_FAULT_MODE=off \
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        up -d \
        --no-deps \
        --force-recreate \
        backend

# ---------------------------------------------------------------------------
# 3. Immediate postcondition validation.
# ---------------------------------------------------------------------------

POST_BACKEND_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q backend
)"

POST_FRONTEND_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q frontend
)"

POST_CADDY_ID="$(
    docker compose \
        --env-file runtime.env \
        -f "$COMPOSE_FILE" \
        ps -q caddy
)"

[[ -n "$POST_BACKEND_ID" ]] || fail "backend container missing after recovery"

POST_FAULT_MODE="$(get_container_env "$POST_BACKEND_ID" TASKFLOW_P4_FAULT_MODE)" \
    || fail "post-recovery TASKFLOW_P4_FAULT_MODE is missing"

POST_ENVIRONMENT="$(get_container_env "$POST_BACKEND_ID" TASKFLOW_ENVIRONMENT)" \
    || fail "post-recovery TASKFLOW_ENVIRONMENT is missing"

POST_PROJECT="$(
    docker inspect "$POST_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project"}}'
)"

POST_WORKDIR="$(
    docker inspect "$POST_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}'
)"

POST_CONFIG_FILES="$(
    docker inspect "$POST_BACKEND_ID" \
        --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'
)"

POST_IMAGE_ID="$(
    docker inspect "$POST_BACKEND_ID" \
        --format '{{.Image}}'
)"

POST_IMAGE_REF="$(
    docker inspect "$POST_BACKEND_ID" \
        --format '{{.Config.Image}}'
)"

POST_RUNTIME_ENV_SHA="$(
    sha256sum "$RUNTIME_DIR/runtime.env" |
        cut -d' ' -f1
)"

docker inspect "$POST_BACKEND_ID" \
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    sed '/^TASKFLOW_P4_FAULT_MODE=/d' |
    sort >"$POST_ENV_FILE"

[[ "$POST_FAULT_MODE" == "off" ]] \
    || fail "post-recovery fault mode is not off"

[[ "$POST_ENVIRONMENT" == "$ENVIRONMENT" ]] \
    || fail "post-recovery environment changed"

[[ "$POST_PROJECT" == "$COMPOSE_PROJECT" ]] \
    || fail "post-recovery compose project changed"

[[ "$POST_WORKDIR" == "$RUNTIME_DIR" ]] \
    || fail "post-recovery working directory changed"

[[ "$POST_CONFIG_FILES" == "$COMPOSE_FILE" ]] \
    || fail "post-recovery compose configuration changed"

[[ "$POST_BACKEND_ID" != "$PRE_BACKEND_ID" ]] \
    || fail "backend was not recreated"

[[ "$POST_FRONTEND_ID" == "$PRE_FRONTEND_ID" ]] \
    || fail "frontend container changed"

[[ "$POST_CADDY_ID" == "$PRE_CADDY_ID" ]] \
    || fail "caddy container changed"

[[ "$POST_IMAGE_ID" == "$PRE_IMAGE_ID" ]] \
    || fail "backend image changed"

[[ "$POST_IMAGE_REF" == "$PRE_IMAGE_REF" ]] \
    || fail "backend image reference changed"

[[ "$POST_RUNTIME_ENV_SHA" == "$PRE_RUNTIME_ENV_SHA" ]] \
    || fail "runtime.env changed"

cmp -s "$PRE_ENV_FILE" "$POST_ENV_FILE" \
    || fail "runtime variables other than TASKFLOW_P4_FAULT_MODE changed"

RESULT="mutation_and_postconditions_verified"

echo "RECOVERY_ACTION=$ACTION_ID"
echo "RECOVERY_MUTATION=backend_only"
echo "POSTCONDITIONS=PASS"
echo "POST_BACKEND_ID=$POST_BACKEND_ID"
echo "POST_FRONTEND_ID=$POST_FRONTEND_ID"
echo "POST_CADDY_ID=$POST_CADDY_ID"
echo "POST_FAULT_MODE=$POST_FAULT_MODE"
echo "POST_IMAGE_REF=$POST_IMAGE_REF"

# ---------------------------------------------------------------------------
# 4. Audit record.
#    The executor emits a bounded, secret-free record for the caller to retain.
# ---------------------------------------------------------------------------

python3 - "$RESULT" "$INCIDENT_ID" "$AUTHORIZATION_ID" "$APPROVER" "$AUTH_AUTHORIZED_AT" "$EXECUTION_TIMESTAMP" <<'PY'
import json
import sys

(
    result,
    incident_id,
    authorization_id,
    approver,
    authorized_at,
    execution_timestamp,
) = sys.argv[1:]

print("=== RECOVERY AUDIT ===")
print(json.dumps({
    "incident_id": incident_id,
    "proposed_action": "recover_task_list_dev_fault",
    "authorization_id": authorization_id,
    "authorization_decision": "approved",
    "approver": approver,
    "authorization_timestamp": authorized_at,
    "execution_timestamp": execution_timestamp,
    "actual_action": "TASKFLOW_P4_FAULT_MODE=list_fail->off; recreate backend only",
    "recovery_result": result,
}, indent=2))
PY
