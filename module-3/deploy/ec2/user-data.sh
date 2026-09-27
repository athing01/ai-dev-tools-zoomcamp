#!/bin/bash
set -Eeuo pipefail

RELEASE_BUCKET="${1:?usage: $0 <release-bucket> [region] [bundle-key]}"
AWS_REGION="${2:-ap-southeast-1}"
BUNDLE_KEY="${3:-deploy/taskflow-runtime.tar.gz}"

DEPLOY_DIR="/opt/taskflow"
COMPOSE_VERSION="v5.5.0"
COMPOSE_PLUGIN_DIR="/usr/local/lib/docker/cli-plugins"
COMPOSE_PLUGIN_PATH="${COMPOSE_PLUGIN_DIR}/docker-compose"

install -d -m 0755 "$DEPLOY_DIR" "$COMPOSE_PLUGIN_DIR"

dnf install -y docker curl-minimal tar

systemctl enable --now docker

compose_tmp="$(mktemp /tmp/taskflow-compose.XXXXXX)"
bundle_tmp="$(mktemp /tmp/taskflow-bundle.XXXXXX.tar.gz)"

cleanup() {
    rm -f "$compose_tmp" "$bundle_tmp"
}
trap cleanup EXIT

curl -fsSL \
    "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o "$compose_tmp"

chmod 0755 "$compose_tmp"
install -m 0755 "$compose_tmp" "$COMPOSE_PLUGIN_PATH"

if systemctl list-unit-files amazon-ssm-agent.service >/dev/null 2>&1; then
    systemctl enable amazon-ssm-agent
    systemctl start amazon-ssm-agent
fi

aws s3 cp \
    --region "$AWS_REGION" \
    --only-show-errors \
    "s3://${RELEASE_BUCKET}/${BUNDLE_KEY}" \
    "$bundle_tmp"

tar -xzf "$bundle_tmp" \
    -C "$DEPLOY_DIR" \
    --no-same-owner \
    deploy.sh \
    Caddyfile \
    docker-compose.ec2.yml

chmod 0755 "$DEPLOY_DIR/deploy.sh"
chmod 0644 "$DEPLOY_DIR/Caddyfile" "$DEPLOY_DIR/docker-compose.ec2.yml"

docker --version
docker compose version
systemctl is-active --quiet docker

aws ssm get-parameters \
    --region "$AWS_REGION" \
    --names \
        /taskflow/database/username \
        /taskflow/database/password \
        /taskflow/database/name \
        /taskflow/caddy/acme-email \
    --with-decryption \
    --query 'Parameters[].Name' \
    --output text >/dev/null

echo "TaskFlow EC2 bootstrap complete."
