#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly SCRIPT_VERSION="1"
readonly AWS_REGION="ap-southeast-1"

# M4 DEV only. This runbook is intentionally separate from the AI responder
# action allowlist and is manually authorized by an external authorization file.
readonly RELEASE_BUCKET="taskflow-releaseartifactbucket-ah8yzqh3idur"
readonly MANIFEST_PREFIX="manifests/m4"
readonly RELEASE_STATE_PREFIX="release-state/m4/dev"

readonly SSM_APP_TAG_KEY="tag:TaskFlowM4"
readonly SSM_APP_TAG_VALUE="true"
readonly SSM_ENV_TAG_KEY="tag:Environment"
readonly SSM_ENV_TAG_VALUE="dev"

readonly DEPLOY_DIR="/opt/taskflow-m4-dev"
readonly DEPLOY_SCRIPT="${DEPLOY_DIR}/deploy.sh"

readonly APP_HOST="dev-app.zctaskflow.athing.cc"
readonly API_URL="https://dev-api.zctaskflow.athing.cc/api/tasks"

readonly TARGET_SCOPE="taskflow-m4-dev-application-rollback"
readonly AUTH_MAX_AGE_SECONDS=3600

usage() {
    cat >&2 <<'USAGE'
Usage:
  rollback.sh <authorization-json> <target-release-sha>

Purpose:
  Execute a manually authorized, bounded M4 DEV application rollback
  to an existing immutable release artifact.

Authorization JSON must contain exactly:
  decision
  approver
  authorized_at
  scope
  environment
  target_release_sha
  migration_compatibility_reviewed
  infrastructure_compatibility_reviewed

The target release must already exist as:
  manifests/m4/<release-sha>.json
  release-state/m4/dev/<release-sha>.json

The rollback reuses the existing M4 deploy engine:
  /opt/taskflow-m4-dev/deploy.sh

This script does not:
  - build application images
  - modify source code
  - modify CloudFormation
  - modify IAM
  - perform database downgrade
  - execute arbitrary commands
USAGE
    exit 2
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ "$#" -eq 2 ]] || usage

readonly AUTH_FILE="$1"
readonly TARGET_SHA="$2"

[[ -f "$AUTH_FILE" ]] || fail "authorization file not found: $AUTH_FILE"
[[ ! -L "$AUTH_FILE" ]] || fail "authorization file must not be a symlink"

[[ "$TARGET_SHA" =~ ^[0-9a-f]{40}$ ]] \
    || fail "target release SHA must be exactly 40 lowercase hexadecimal characters"

for command in aws curl jq python3; do
    command -v "$command" >/dev/null 2>&1 \
        || fail "required command not found: $command"
done

AWS_CMD=(aws --region "$AWS_REGION")
if [[ -n "${AWS_PROFILE:-}" ]]; then
    AWS_CMD+=(--profile "$AWS_PROFILE")
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

readonly MANIFEST_FILE="${TMP_DIR}/rollback-manifest.json"
readonly TARGET_STATE_FILE="${TMP_DIR}/rollback-release-state.json"
readonly BASELINE_API_FILE="${TMP_DIR}/baseline-api.json"
readonly FINAL_STATE_FILE="${TMP_DIR}/final-release-state.json"

# ---------------------------------------------------------------------------
# 1. Validate external/manual authorization.
# ---------------------------------------------------------------------------

python3 - "$AUTH_FILE" "$TARGET_SHA" "$TARGET_SCOPE" "$AUTH_MAX_AGE_SECONDS" <<'PY'
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

auth_path = Path(sys.argv[1])
target_sha = sys.argv[2]
expected_scope = sys.argv[3]
max_age_seconds = int(sys.argv[4])

data = json.loads(auth_path.read_text(encoding="utf-8"))

required = {
    "decision",
    "approver",
    "authorized_at",
    "scope",
    "environment",
    "target_release_sha",
    "migration_compatibility_reviewed",
    "infrastructure_compatibility_reviewed",
}

missing = required - data.keys()
extra = set(data) - required

if missing:
    raise SystemExit(f"authorization missing fields: {sorted(missing)}")

if extra:
    raise SystemExit(f"authorization contains unexpected fields: {sorted(extra)}")

if data["decision"] != "approved":
    raise SystemExit("authorization decision must be approved")

if data["scope"] != expected_scope:
    raise SystemExit("authorization scope mismatch")

if data["environment"] != "dev":
    raise SystemExit("authorization environment must be dev")

if data["target_release_sha"] != target_sha:
    raise SystemExit("authorization target_release_sha does not match requested target")

if not data["migration_compatibility_reviewed"]:
    raise SystemExit("migration compatibility review is required")

if not data["infrastructure_compatibility_reviewed"]:
    raise SystemExit("infrastructure compatibility review is required")

approver = data["approver"]
if not isinstance(approver, str) or not approver.strip():
    raise SystemExit("approver must be a non-empty string")

if "\n" in approver or "\r" in approver:
    raise SystemExit("approver must not contain newline characters")

try:
    authorized_at = datetime.fromisoformat(
        data["authorized_at"].replace("Z", "+00:00")
    )
except ValueError as exc:
    raise SystemExit("authorized_at must be RFC3339") from exc

if authorized_at.tzinfo is None:
    raise SystemExit("authorized_at must include timezone")

now = datetime.now(timezone.utc)

if authorized_at > now + timedelta(seconds=60):
    raise SystemExit("authorization timestamp is in the future")

if now - authorized_at > timedelta(seconds=max_age_seconds):
    raise SystemExit("authorization has expired")

print("External authorization: PASS")
print(f"approver={approver}")
print(f"authorized_at={data['authorized_at']}")
print(f"target_release_sha={target_sha}")
PY

# ---------------------------------------------------------------------------
# 2. Discover current M4 DEV release state.
# ---------------------------------------------------------------------------

CURRENT_STATE_LIST="$(
    "${AWS_CMD[@]}" s3api list-objects-v2 \
        --bucket "$RELEASE_BUCKET" \
        --prefix "${RELEASE_STATE_PREFIX}/" \
        --output json
)"

CURRENT_STATE_KEY="$(
    python3 - "$CURRENT_STATE_LIST" <<'PY'
import json
import re
import sys

data = json.loads(sys.argv[1])
pattern = re.compile(r"^release-state/m4/dev/[0-9a-f]{40}\.json$")

candidates = [
    item for item in data.get("Contents", [])
    if pattern.fullmatch(item["Key"])
]

if not candidates:
    raise SystemExit("no valid M4 DEV release-state objects found")

latest = max(candidates, key=lambda item: item["LastModified"])
print(latest["Key"])
PY
)"

readonly CURRENT_SHA="${CURRENT_STATE_KEY##*/}"
readonly CURRENT_SHA="${CURRENT_SHA%.json}"

[[ "$CURRENT_SHA" != "$TARGET_SHA" ]] \
    || fail "target release is already the latest M4 DEV release"

echo "Current M4 DEV release: ${CURRENT_SHA}"
echo "Rollback target: ${TARGET_SHA}"

# ---------------------------------------------------------------------------
# 3. Baseline public service before mutation.
# ---------------------------------------------------------------------------

FRONTEND_STATUS="$(
    curl \
        --silent \
        --show-error \
        --location \
        --connect-timeout 10 \
        --max-time 20 \
        --output /dev/null \
        --write-out '%{http_code}' \
        "https://${APP_HOST}/"
)"

[[ "$FRONTEND_STATUS" == "200" ]] \
    || fail "baseline frontend check failed: HTTP ${FRONTEND_STATUS}"

API_STATUS="$(
    curl \
        --silent \
        --show-error \
        --location \
        --connect-timeout 10 \
        --max-time 20 \
        --output "$BASELINE_API_FILE" \
        --write-out '%{http_code}' \
        "$API_URL"
)"

[[ "$API_STATUS" == "200" ]] \
    || fail "baseline API check failed: HTTP ${API_STATUS}"

jq -e 'type == "array"' "$BASELINE_API_FILE" >/dev/null \
    || fail "baseline API response is not a JSON array"

echo "Baseline service: PASS"

# ---------------------------------------------------------------------------
# 4. Fetch and validate the target immutable release artifacts.
# ---------------------------------------------------------------------------

readonly MANIFEST_KEY="${MANIFEST_PREFIX}/${TARGET_SHA}.json"
readonly TARGET_STATE_KEY="${RELEASE_STATE_PREFIX}/${TARGET_SHA}.json"

echo "Fetching target release manifest..."
"${AWS_CMD[@]}" s3 cp \
    "s3://${RELEASE_BUCKET}/${MANIFEST_KEY}" \
    "$MANIFEST_FILE" \
    >/dev/null

echo "Fetching target release-state..."
"${AWS_CMD[@]}" s3 cp \
    "s3://${RELEASE_BUCKET}/${TARGET_STATE_KEY}" \
    "$TARGET_STATE_FILE" \
    >/dev/null

jq -e \
    --arg sha "$TARGET_SHA" \
    '
      .git_sha == $sha and
      .artifact_tag == ("sha-" + $sha) and
      (.backend_image | test("/taskflow/backend$")) and
      (.frontend_image | test("/taskflow/frontend$")) and
      (.backend_digest | test("^sha256:[0-9a-f]{64}$")) and
      (.frontend_digest | test("^sha256:[0-9a-f]{64}$"))
    ' \
    "$MANIFEST_FILE" \
    >/dev/null \
    || fail "target release manifest validation failed"

readonly BACKEND_IMAGE="$(jq -r '.backend_image' "$MANIFEST_FILE")"
readonly BACKEND_DIGEST="$(jq -r '.backend_digest' "$MANIFEST_FILE")"
readonly FRONTEND_IMAGE="$(jq -r '.frontend_image' "$MANIFEST_FILE")"
readonly FRONTEND_DIGEST="$(jq -r '.frontend_digest' "$MANIFEST_FILE")"

readonly EXPECTED_BACKEND_IMAGE="${BACKEND_IMAGE}@${BACKEND_DIGEST}"
readonly EXPECTED_FRONTEND_IMAGE="${FRONTEND_IMAGE}@${FRONTEND_DIGEST}"

jq -e \
    --arg sha "$TARGET_SHA" \
    --arg backend "$EXPECTED_BACKEND_IMAGE" \
    --arg frontend "$EXPECTED_FRONTEND_IMAGE" \
    '
      .git_sha == $sha and
      .backend_image == $backend and
      .frontend_image == $frontend
    ' \
    "$TARGET_STATE_FILE" \
    >/dev/null \
    || fail "target release-state does not match target manifest"

echo "Target manifest/state: PASS"

# ---------------------------------------------------------------------------
# 5. Verify immutable ECR digests still exist.
# ---------------------------------------------------------------------------

"${AWS_CMD[@]}" ecr describe-images \
    --repository-name taskflow/backend \
    --image-ids "imageDigest=${BACKEND_DIGEST}" \
    --query 'imageDetails[0].imageDigest' \
    --output text \
    | grep -Fx "$BACKEND_DIGEST" \
    >/dev/null \
    || fail "target backend digest is not present in ECR"

"${AWS_CMD[@]}" ecr describe-images \
    --repository-name taskflow/frontend \
    --image-ids "imageDigest=${FRONTEND_DIGEST}" \
    --query 'imageDetails[0].imageDigest' \
    --output text \
    | grep -Fx "$FRONTEND_DIGEST" \
    >/dev/null \
    || fail "target frontend digest is not present in ECR"

echo "Immutable ECR artifacts: PASS"

# ---------------------------------------------------------------------------
# 6. Manual review boundary.
#
# Migration/infrastructure compatibility are intentionally represented by the
# external authorization record rather than inferred from model output.
# ---------------------------------------------------------------------------

echo "Compatibility review: externally authorized"

# ---------------------------------------------------------------------------
# 7. Construct the fixed M4 DEV deployment command.
# ---------------------------------------------------------------------------

readonly DEPLOY_COMMAND="$(
    printf \
        'exec env TASKFLOW_RELEASE_BUCKET=%q TASKFLOW_APP_HOST=%q TASKFLOW_API_HOST=%q TASKFLOW_SSM_PARAMETER_PREFIX=%q DEPLOY_DIR=%q RELEASE_STATE_PREFIX=%q AWS_REGION=%q %q %q' \
        "$RELEASE_BUCKET" \
        "$APP_HOST" \
        "dev-api.zctaskflow.athing.cc" \
        "/taskflow/m4/dev" \
        "$DEPLOY_DIR" \
        "$RELEASE_STATE_PREFIX" \
        "$AWS_REGION" \
        "$DEPLOY_SCRIPT" \
        "$MANIFEST_KEY"
)"

echo "Deployment engine: ${DEPLOY_SCRIPT}"
echo "Manifest key: ${MANIFEST_KEY}"

# ---------------------------------------------------------------------------
# 8. Execute through SSM against the fixed M4 DEV tag scope.
# ---------------------------------------------------------------------------

SSM_REQUEST="$(
    jq -n \
        --arg command "$DEPLOY_COMMAND" \
        --arg comment "Manual authorized M4 DEV rollback to ${TARGET_SHA}" \
        '{
          DocumentName: "AWS-RunShellScript",
          Targets: [
            {
              Key: "tag:TaskFlowM4",
              Values: ["true"]
            },
            {
              Key: "tag:Environment",
              Values: ["dev"]
            }
          ],
          Parameters: {
            commands: [$command]
          },
          Comment: $comment,
          MaxConcurrency: "1",
          MaxErrors: "0",
          TimeoutSeconds: 3600
        }'
)"

COMMAND_ID="$(
    "${AWS_CMD[@]}" ssm send-command \
        --cli-input-json "$SSM_REQUEST" \
        --query 'Command.CommandId' \
        --output text
)"

[[ "$COMMAND_ID" =~ ^[A-Za-z0-9-]+$ ]] \
    || fail "SSM did not return a valid command ID"

echo "SSM command ID: ${COMMAND_ID}"

INSTANCE_ID=""
SSM_STATUS=""

for attempt in $(seq 1 360); do
    INVOCATIONS="$(
        "${AWS_CMD[@]}" ssm list-command-invocations \
            --command-id "$COMMAND_ID" \
            --details \
            --output json
    )"

    COUNT="$(jq 'length' <<<"$INVOCATIONS")"

    if [[ "$COUNT" -eq 0 ]]; then
        echo "SSM invocation pending target resolution (${attempt}/360)"
        sleep 10
        continue
    fi

    [[ "$COUNT" -eq 1 ]] \
        || fail "expected exactly one M4 DEV SSM invocation, got ${COUNT}"

    INSTANCE_ID="$(jq -r '.[0].InstanceId' <<<"$INVOCATIONS")"
    SSM_STATUS="$(jq -r '.[0].Status' <<<"$INVOCATIONS")"

    case "$SSM_STATUS" in
        Success)
            echo "SSM deployment succeeded on ${INSTANCE_ID}"
            break
            ;;

        Pending|InProgress|Delayed)
            echo "SSM status: ${SSM_STATUS} (${attempt}/360)"
            sleep 10
            ;;

        *)
            echo "SSM deployment failed with status: ${SSM_STATUS}" >&2
            "${AWS_CMD[@]}" ssm get-command-invocation \
                --command-id "$COMMAND_ID" \
                --instance-id "$INSTANCE_ID" \
                --query '{
                  Status:Status,
                  ResponseCode:ResponseCode,
                  Stdout:StandardOutputContent,
                  Stderr:StandardErrorContent
                }' \
                --output json \
                >&2 || true
            exit 1
            ;;
    esac

    if [[ "$attempt" -eq 360 ]]; then
        fail "timed out waiting for SSM command ${COMMAND_ID}"
    fi
done

# ---------------------------------------------------------------------------
# 9. Verify the deployment result against the immutable target artifacts.
# ---------------------------------------------------------------------------

"${AWS_CMD[@]}" s3 cp \
    "s3://${RELEASE_BUCKET}/${TARGET_STATE_KEY}" \
    "$FINAL_STATE_FILE" \
    >/dev/null

jq -e \
    --arg sha "$TARGET_SHA" \
    --arg backend "$EXPECTED_BACKEND_IMAGE" \
    --arg frontend "$EXPECTED_FRONTEND_IMAGE" \
    '
      .git_sha == $sha and
      .backend_image == $backend and
      .frontend_image == $frontend
    ' \
    "$FINAL_STATE_FILE" \
    >/dev/null \
    || fail "post-rollback release-state verification failed"

FINAL_FRONTEND_STATUS="$(
    curl \
        --silent \
        --show-error \
        --location \
        --connect-timeout 10 \
        --max-time 20 \
        --output /dev/null \
        --write-out '%{http_code}' \
        "https://${APP_HOST}/"
)"

[[ "$FINAL_FRONTEND_STATUS" == "200" ]] \
    || fail "post-rollback frontend check failed: HTTP ${FINAL_FRONTEND_STATUS}"

FINAL_API_FILE="${TMP_DIR}/final-api.json"

FINAL_API_STATUS="$(
    curl \
        --silent \
        --show-error \
        --location \
        --connect-timeout 10 \
        --max-time 20 \
        --output "$FINAL_API_FILE" \
        --write-out '%{http_code}' \
        "$API_URL"
)"

[[ "$FINAL_API_STATUS" == "200" ]] \
    || fail "post-rollback API check failed: HTTP ${FINAL_API_STATUS}"

jq -e 'type == "array"' "$FINAL_API_FILE" >/dev/null \
    || fail "post-rollback API response is not a JSON array"

# ---------------------------------------------------------------------------
# 10. Secret-free audit record.
# ---------------------------------------------------------------------------

python3 - \
    "$SCRIPT_VERSION" \
    "$CURRENT_SHA" \
    "$TARGET_SHA" \
    "$MANIFEST_KEY" \
    "$COMMAND_ID" \
    "$INSTANCE_ID" \
    "$FINAL_FRONTEND_STATUS" \
    "$FINAL_API_STATUS" \
    "$TARGET_STATE_KEY" <<'PY'
import json
import sys

(
    version,
    current_sha,
    target_sha,
    manifest_key,
    command_id,
    instance_id,
    frontend_status,
    api_status,
    state_key,
) = sys.argv[1:]

record = {
    "runbook": "taskflow-m4-incident-response/rollback.sh",
    "version": version,
    "scope": "taskflow-m4-dev",
    "authorization": "external_manual",
    "current_release_sha": current_sha,
    "target_release_sha": target_sha,
    "manifest_key": manifest_key,
    "ssm_command_id": command_id,
    "instance_id": instance_id,
    "release_state_key": state_key,
    "verification": {
        "frontend_http_status": frontend_status,
        "api_http_status": api_status,
        "api_json_array": True,
        "result": "verified",
    },
}

print("=== ROLLBACK AUDIT ===")
print(json.dumps(record, indent=2))
PY

echo "ROLLBACK_RESULT=verified"
