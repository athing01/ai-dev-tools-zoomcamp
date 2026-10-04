#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly AWS_REGION="${AWS_REGION:-ap-southeast-1}"

readonly TASKFLOW_RELEASE_BUCKET="${TASKFLOW_RELEASE_BUCKET:?TASKFLOW_RELEASE_BUCKET is required}"
readonly MANIFEST_KEY="${1:?usage: deploy.sh <manifest-key>}"

readonly TASKFLOW_RDS_HOST="${TASKFLOW_RDS_HOST:-taskflow.c1a6masuo5g2.ap-southeast-1.rds.amazonaws.com}"

readonly TASKFLOW_APP_HOST="${TASKFLOW_APP_HOST:?TASKFLOW_APP_HOST is required}"
readonly TASKFLOW_API_HOST="${TASKFLOW_API_HOST:?TASKFLOW_API_HOST is required}"
readonly TASKFLOW_SSM_PARAMETER_PREFIX="${TASKFLOW_SSM_PARAMETER_PREFIX:?TASKFLOW_SSM_PARAMETER_PREFIX is required}"
readonly DEPLOY_DIR="${DEPLOY_DIR:?DEPLOY_DIR is required}"
readonly RELEASE_STATE_PREFIX="${RELEASE_STATE_PREFIX:?RELEASE_STATE_PREFIX is required}"

readonly ECR_REGISTRY="${ECR_REGISTRY:-060622563960.dkr.ecr.ap-southeast-1.amazonaws.com}"
readonly BACKEND_REPO="${BACKEND_REPO:-${ECR_REGISTRY}/taskflow/backend}"
readonly FRONTEND_REPO="${FRONTEND_REPO:-${ECR_REGISTRY}/taskflow/frontend}"

readonly COMPOSE_FILE="${DEPLOY_DIR}/docker-compose.ec2.yml"
readonly RUNTIME_ENV="${DEPLOY_DIR}/runtime.env"
readonly LOCK_DIR="${DEPLOY_DIR}/.deploy.lock"

[[ "$MANIFEST_KEY" == manifests/m4/*.json ]] \
    || fail "M4 manifest key required: manifests/m4/<release-sha>.json"

[[ "$TASKFLOW_SSM_PARAMETER_PREFIX" =~ ^/taskflow/m4/(dev|prod)$ ]] \
    || fail "invalid M4 SSM parameter prefix"

[[ "$RELEASE_STATE_PREFIX" =~ ^release-state/m4/(dev|prod)$ ]] \
    || fail "invalid M4 release-state prefix"

readonly TASKFLOW_ENVIRONMENT="${TASKFLOW_SSM_PARAMETER_PREFIX##*/}"

MANIFEST_FILE=""
STATE_FILE=""
DOCKER_LOGOUT_NEEDED=0

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

cleanup() {
    rm -f "${MANIFEST_FILE:-}" "${STATE_FILE:-}"
    if [[ "${DOCKER_LOGOUT_NEEDED}" == "1" ]]; then
        docker logout "${ECR_REGISTRY}" >/dev/null 2>&1 || true
    fi
    rmdir "$LOCK_DIR" 2>/dev/null || true
}
trap cleanup EXIT

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

require_command aws
require_command docker
require_command python3
require_command curl

[[ -f "$COMPOSE_FILE" ]] || fail "missing Compose file: $COMPOSE_FILE"
[[ -f "$DEPLOY_DIR/Caddyfile" ]] || fail "missing Caddyfile: $DEPLOY_DIR/Caddyfile"

mkdir -p "$DEPLOY_DIR"

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    fail "another deployment is already running"
fi

docker compose version >/dev/null 2>&1 \
    || fail "Docker Compose plugin is unavailable"

MANIFEST_FILE="$(mktemp "${DEPLOY_DIR}/manifest.XXXXXX.json")"
STATE_FILE="$(mktemp "${DEPLOY_DIR}/release-state.XXXXXX.json")"
chmod 600 "$MANIFEST_FILE" "$STATE_FILE"

echo "Fetching release manifest..."
aws s3 cp \
    --region "$AWS_REGION" \
    --only-show-errors \
    "s3://${TASKFLOW_RELEASE_BUCKET}/${MANIFEST_KEY}" \
    "$MANIFEST_FILE"

readarray -t MANIFEST_VALUES < <(
    python3 - "$MANIFEST_FILE" <<'PY'
import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())

git_sha = data.get("git_sha")
backend_digest = data.get("backend_digest")
frontend_digest = data.get("frontend_digest")

if not isinstance(git_sha, str) or not re.fullmatch(r"[0-9a-f]{7,64}", git_sha):
    raise SystemExit("invalid git_sha in release manifest")

for name, value in (
    ("backend_digest", backend_digest),
    ("frontend_digest", frontend_digest),
):
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise SystemExit(f"invalid {name} in release manifest")

print(git_sha)
print(backend_digest)
print(frontend_digest)
PY
)

[[ "${#MANIFEST_VALUES[@]}" -eq 3 ]] || fail "invalid release manifest"

readonly GIT_SHA="${MANIFEST_VALUES[0]}"
readonly BACKEND_DIGEST="${MANIFEST_VALUES[1]}"
readonly FRONTEND_DIGEST="${MANIFEST_VALUES[2]}"

readonly BACKEND_IMAGE="${BACKEND_REPO}@${BACKEND_DIGEST}"
readonly FRONTEND_IMAGE="${FRONTEND_REPO}@${FRONTEND_DIGEST}"

echo "Release: ${GIT_SHA}"
echo "Backend: ${BACKEND_DIGEST}"
echo "Frontend: ${FRONTEND_DIGEST}"

echo "Authenticating to ECR..."
aws ecr get-login-password --region "$AWS_REGION" |
    docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null
DOCKER_LOGOUT_NEEDED=1

echo "Pulling exact backend image..."
docker pull "$BACKEND_IMAGE"

echo "Pulling exact frontend image..."
docker pull "$FRONTEND_IMAGE"

docker logout "$ECR_REGISTRY" >/dev/null 2>&1 || true
DOCKER_LOGOUT_NEEDED=0

echo "Retrieving runtime parameters..."

DB_USER="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${TASKFLOW_SSM_PARAMETER_PREFIX}/database/username" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text)"

DB_PASSWORD="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${TASKFLOW_SSM_PARAMETER_PREFIX}/database/password" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text)"

DB_NAME="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${TASKFLOW_SSM_PARAMETER_PREFIX}/database/name" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text)"

ACME_EMAIL="$(aws ssm get-parameter \
    --region "$AWS_REGION" \
    --name "${TASKFLOW_SSM_PARAMETER_PREFIX}/caddy/acme-email" \
    --query 'Parameter.Value' \
    --output text)"

if [[ "$TASKFLOW_ENVIRONMENT" == "dev" ]]; then
    OTEL_EXPORTER_OTLP_ENDPOINT="$(aws ssm get-parameter \
        --region "$AWS_REGION" \
        --name "${TASKFLOW_SSM_PARAMETER_PREFIX}/observability/otlp-endpoint" \
        --query 'Parameter.Value' \
        --output text)"

    [[ "$OTEL_EXPORTER_OTLP_ENDPOINT" != *$'\n'* && \
       "$OTEL_EXPORTER_OTLP_ENDPOINT" != *$'\r'* ]] \
        || fail "OTEL_EXPORTER_OTLP_ENDPOINT contains a newline"
else
    OTEL_EXPORTER_OTLP_ENDPOINT=""
fi

for value_name in DB_USER DB_PASSWORD DB_NAME ACME_EMAIL OTEL_EXPORTER_OTLP_ENDPOINT; do
    value="${!value_name}"
    [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] \
        || fail "${value_name} contains a newline"
done

DATABASE_URL="$(
    DB_USER="$DB_USER" \
    DB_PASSWORD="$DB_PASSWORD" \
    DB_NAME="$DB_NAME" \
    DB_HOST="$TASKFLOW_RDS_HOST" \
    python3 <<'PY'
import os
from urllib.parse import quote

user = quote(os.environ["DB_USER"], safe="")
password = quote(os.environ["DB_PASSWORD"], safe="")
name = quote(os.environ["DB_NAME"], safe="")
host = os.environ["DB_HOST"]

print(
    f"postgresql+psycopg://{user}:{password}@{host}:5432/{name}?sslmode=require"
)
PY
)"

cat > "$RUNTIME_ENV" <<EOF_ENV
BACKEND_IMAGE=${BACKEND_IMAGE}
FRONTEND_IMAGE=${FRONTEND_IMAGE}
DATABASE_URL=${DATABASE_URL}
CORS_ALLOWED_ORIGINS=https://${TASKFLOW_APP_HOST}
ACME_EMAIL=${ACME_EMAIL}
TASKFLOW_APP_HOST=${TASKFLOW_APP_HOST}
TASKFLOW_API_HOST=${TASKFLOW_API_HOST}
TASKFLOW_OBSERVABILITY_ENABLED=$([[ "$TASKFLOW_ENVIRONMENT" == "dev" ]] && echo true || echo false)
TASKFLOW_ENVIRONMENT=${TASKFLOW_ENVIRONMENT}
TASKFLOW_RELEASE_SHA=${GIT_SHA}
OTEL_SERVICE_NAME=taskflow-backend
OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
OTEL_METRIC_EXPORT_INTERVAL=30000
OTEL_BLRP_SCHEDULE_DELAY=10000
TASKFLOW_P4_FAULT_MODE=off
EOF_ENV

chmod 600 "$RUNTIME_ENV"

unset DB_USER DB_PASSWORD DB_NAME ACME_EMAIL DATABASE_URL OTEL_EXPORTER_OTLP_ENDPOINT

echo "Verifying RDS reachability..."

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    run --rm --no-deps migrate \
    /app/.venv/bin/python -c '
from sqlalchemy import create_engine, text
import os

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("RDS reachability: OK")
'

echo "Running database migration..."

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    run --rm --no-deps migrate

echo "Updating backend..."

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    up -d --no-deps backend

echo "Waiting for backend readiness..."

backend_ready=0

for _ in $(seq 1 60); do
    if docker compose \
        --env-file "$RUNTIME_ENV" \
        -f "$COMPOSE_FILE" \
        exec -T backend \
        /app/.venv/bin/python -c '
import json
import urllib.request

with urllib.request.urlopen("http://backend:8000/api/tasks", timeout=5) as response:
    if response.status != 200:
        raise SystemExit(1)
    data = json.load(response)

if not isinstance(data, list):
    raise SystemExit(1)
' >/dev/null 2>&1; then
        backend_ready=1
        break
    fi

    sleep 2
done

if [[ "$backend_ready" != "1" ]]; then
    echo "Backend readiness failed." >&2
    docker compose \
        --env-file "$RUNTIME_ENV" \
        -f "$COMPOSE_FILE" \
        logs --tail=100 backend >&2 || true
    exit 1
fi

echo "Backend readiness: OK"

echo "Updating frontend..."

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    up -d --no-deps frontend

echo "Starting Caddy..."

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    up -d --no-deps caddy

echo "Waiting for proxy readiness..."
proxy_ready=0

for _ in $(seq 1 60); do
    app_ok=0
    api_ok=0

    if curl -kfsSL \
        --max-time 5 \
        --max-redirs 5 \
        --resolve "${TASKFLOW_APP_HOST}:80:127.0.0.1" \
        --resolve "${TASKFLOW_APP_HOST}:443:127.0.0.1" \
        "http://${TASKFLOW_APP_HOST}/" \
        -o /dev/null
    then
        app_ok=1
    fi

    api_response="$(mktemp "${DEPLOY_DIR}/api-response.XXXXXX")"
    chmod 600 "$api_response"

    if curl -kfsSL \
        --max-time 5 \
        --max-redirs 5 \
        --resolve "${TASKFLOW_API_HOST}:80:127.0.0.1" \
        --resolve "${TASKFLOW_API_HOST}:443:127.0.0.1" \
        "http://${TASKFLOW_API_HOST}/api/tasks" \
        -o "$api_response" 2>/dev/null
    then
        if python3 - "$api_response" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
raise SystemExit(0 if isinstance(data, list) else 1)
PY
        then
            api_ok=1
        fi
    fi

    rm -f "$api_response"

    if [[ "$app_ok" == "1" && "$api_ok" == "1" ]]; then
        proxy_ready=1
        break
    fi

    sleep 2
done

if [[ "$proxy_ready" != "1" ]]; then
    echo "Proxy readiness failed." >&2
    docker compose \
        --env-file "$RUNTIME_ENV" \
        -f "$COMPOSE_FILE" \
        ps >&2 || true
    docker compose \
        --env-file "$RUNTIME_ENV" \
        -f "$COMPOSE_FILE" \
        logs --tail=100 caddy backend frontend >&2 || true
    exit 1
fi

echo "Proxy readiness: OK"

DEPLOYED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - \
    "$STATE_FILE" \
    "$GIT_SHA" \
    "$BACKEND_IMAGE" \
    "$FRONTEND_IMAGE" \
    "$DEPLOYED_AT" <<'PY'
import json
import sys
from pathlib import Path

path, git_sha, backend_image, frontend_image, deployed_at = sys.argv[1:]

Path(path).write_text(
    json.dumps(
        {
            "git_sha": git_sha,
            "backend_image": backend_image,
            "frontend_image": frontend_image,
            "deployed_at": deployed_at,
        },
        indent=2,
    )
    + "\n"
)
PY

echo "Recording release state..."

aws s3 cp \
    --region "$AWS_REGION" \
    --only-show-errors \
    "$STATE_FILE" \
    "s3://${TASKFLOW_RELEASE_BUCKET}/${RELEASE_STATE_PREFIX}/${GIT_SHA}.json"

echo "Deployment complete: ${GIT_SHA}"

docker compose \
    --env-file "$RUNTIME_ENV" \
    -f "$COMPOSE_FILE" \
    ps
