# TaskFlow Module 3 Release Process

This document is the operational runbook for releasing, rolling back, and recovering the deployed TaskFlow application.

The deployment architecture and configuration boundaries are documented separately in `docs/deployment.md`. Test strategy and local verification remain in `docs/testing.md`.

## 1. Release Model

The normal production release identity is the full Git commit SHA.

Application images are immutable ECR images referenced by digest. A release manifest in S3 binds one Git SHA to its backend and frontend image digests.

The controlled deployment path is:

```text
merge to main
-> CI succeeds for the same commit
-> GitHub Actions obtains AWS credentials through GitHub OIDC
-> build linux/amd64 images
-> push immutable ECR images
-> resolve exact image digests
-> update CloudFormation only when infrastructure files changed
-> create S3 release manifest
-> invoke SSM Run Command
-> EC2 /opt/taskflow/deploy.sh
-> pull exact digests
-> retrieve runtime parameters
-> verify RDS reachability
-> run `alembic upgrade head`
-> update backend/frontend
-> verify readiness
-> record release state
-> public smoke test
```

CloudFormation manages stable infrastructure. It is not the normal application-release mechanism.

## 2. Release Artifacts

Release manifest:

```text
s3://<ReleaseArtifactBucketName>/manifests/<release-SHA>.json
```

Manifest schema:

```json
{
  "git_sha": "<release SHA>",
  "backend_digest": "sha256:<64 hex characters>",
  "frontend_digest": "sha256:<64 hex characters>"
}
```

Release state:

```text
s3://<ReleaseArtifactBucketName>/release-state/<release-SHA>.json
```

Release-state records the latest deployment of a release SHA, including the deployed Git SHA, exact backend/frontend ECR image references, and deployment timestamp.

Do not manually edit a release manifest or release-state object.
Rollback reuses the existing release manifest associated with the target release SHA.

## 3. Normal Release

A normal release starts from a successful CI run for the same commit that is being released from `main`.

The deployment workflow:

1. Uses `workflow_run.head_sha` as the sole release SHA.
2. Rejects PR deployment paths by requiring the upstream CI event to be a successful `push` to `main`.
3. Builds backend and frontend images for `linux/amd64`.
4. Pushes immutable `sha-<full-SHA>` tags to ECR.
5. Resolves and records image digests.
6. Checks whether `module-3/infra/**` changed in the release range.
7. Runs CloudFormation only when infrastructure changes are present.
8. Uploads the release manifest to S3.
9. Invokes `AWS-RunShellScript` through SSM.
10. Waits for the EC2 deployment command to succeed.
11. Verifies the release-state object against the same SHA and exact image digests.
12. Verifies the public frontend and API smoke checks.

The release SHA must never be substituted with another commit SHA.

The production release model should use a merge commit or a single-commit push to `main`. The infrastructure-change check compares `RELEASE_SHA^..RELEASE_SHA`; a multi-commit direct push can omit infrastructure changes introduced by earlier commits in the same push.

## 4. Pre-Release Checks

Before a manual rollback or recovery, resolve the current release artifact bucket and EC2 instance from the deployed CloudFormation stack:

```bash
set -euo pipefail

RELEASE_BUCKET=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`ReleaseArtifactBucketName`].OutputValue' \
    --output text
)

EC2_INSTANCE_ID=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`Ec2InstanceId`].OutputValue' \
    --output text
)
```

Confirm the EC2 instance is online:

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$EC2_INSTANCE_ID" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query 'InstanceInformationList[].{InstanceId:InstanceId,PingStatus:PingStatus,Platform:PlatformName}' \
  --output table
```

Expected:

```text
one instance
PingStatus = Online
```

List the release-state objects ordered by last modification time and identify the most recently deployed release before changing production. Then inspect its release-state content to confirm the deployed Git SHA and image references.

```bash
aws s3api list-objects-v2 \
  --bucket "$RELEASE_BUCKET" \
  --prefix "release-state/" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query 'reverse(sort_by(Contents,&LastModified))[].{Key:Key,LastModified:LastModified}' \
  --output table
```

For a planned rollback or rehearsal, verify the current release-state and public service before changing production:

```bash
CURRENT_SHA="<current-release-SHA>"

aws s3 cp \
  "s3://$RELEASE_BUCKET/release-state/${CURRENT_SHA}.json" \
  - \
  --region ap-southeast-1 \
  --profile taskflow | jq .
```

```bash
FRONTEND_STATUS="$(
  curl -fsS -o /dev/null -w '%{http_code}' \
    https://app.zctaskflow.athing.cc/
)"

API_TYPE="$(
  curl -fsS \
    https://api.zctaskflow.athing.cc/api/tasks | jq -r 'type'
)"

printf 'frontend = %s\n' "$FRONTEND_STATUS"
printf 'API = %s\n' "$API_TYPE"

[[ "$FRONTEND_STATUS" == "200" ]]
[[ "$API_TYPE" == "array" ]]
```

Expected:

```text
frontend = 200
API = array
```

Inspect the selected target manifest and release-state:

```bash
set -euo pipefail

ROLLBACK_SHA="<previous-release-SHA>"
CURRENT_SHA="<current-release-SHA>"

aws s3 cp \
  "s3://$RELEASE_BUCKET/manifests/${ROLLBACK_SHA}.json" \
  rollback-manifest.json \
  --region ap-southeast-1 \
  --profile taskflow

aws s3 cp \
  "s3://$RELEASE_BUCKET/release-state/${ROLLBACK_SHA}.json" \
  rollback-release-state.json \
  --region ap-southeast-1 \
  --profile taskflow
```

Validate the target manifest before using it:

```bash
jq -e \
  --arg sha "$ROLLBACK_SHA" \
  '
    .git_sha == $sha and
    (.backend_digest | test("^sha256:[0-9a-f]{64}$")) and
    (.frontend_digest | test("^sha256:[0-9a-f]{64}$"))
  ' \
  rollback-manifest.json > /dev/null
```

Read the exact image digests from the validated manifest:

```bash
BACKEND_DIGEST="$(jq -r '.backend_digest' rollback-manifest.json)"
FRONTEND_DIGEST="$(jq -r '.frontend_digest' rollback-manifest.json)"
```

Verify that the target release-state belongs to the target SHA and records the exact images from the manifest:

```bash
BACKEND_ECR_URI=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`BackendEcrRepositoryUri`].OutputValue' \
    --output text
)

FRONTEND_ECR_URI=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendEcrRepositoryUri`].OutputValue' \
    --output text
)

[[ -n "$BACKEND_ECR_URI" && "$BACKEND_ECR_URI" != "None" ]]
[[ -n "$FRONTEND_ECR_URI" && "$FRONTEND_ECR_URI" != "None" ]]

EXPECTED_BACKEND_IMAGE="${BACKEND_ECR_URI}@${BACKEND_DIGEST}"
EXPECTED_FRONTEND_IMAGE="${FRONTEND_ECR_URI}@${FRONTEND_DIGEST}"

jq -e \
  --arg git_sha "$ROLLBACK_SHA" \
  --arg backend_image "$EXPECTED_BACKEND_IMAGE" \
  --arg frontend_image "$EXPECTED_FRONTEND_IMAGE" \
  '
    .git_sha == $git_sha and
    .backend_image == $backend_image and
    .frontend_image == $frontend_image
  ' \
  rollback-release-state.json > /dev/null
```

Also confirm both image digests still exist in ECR. A rollback must not depend on rebuilding an old release:

```bash
aws ecr describe-images \
  --repository-name taskflow/backend \
  --image-ids "imageDigest=$BACKEND_DIGEST" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query 'imageDetails[0].{digest:imageDigest,pushedAt:imagePushedAt}' \
  --output table

aws ecr describe-images \
  --repository-name taskflow/frontend \
  --image-ids "imageDigest=$FRONTEND_DIGEST" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query 'imageDetails[0].{digest:imageDigest,pushedAt:imagePushedAt}' \
  --output table
```

Review any migration changes between the current release and the rollback target before proceeding:

```bash
git diff --name-status \
  "$ROLLBACK_SHA" \
  "$CURRENT_SHA" \
  -- module-3/backend/alembic
```

An empty Alembic migration diff was sufficient for the P10 rehearsal, but it is not by itself a general proof of application compatibility.

## 5. Rollback Procedure

### 5.1 Select the rollback target

Choose a previously deployed release with:

- an existing S3 manifest
- an existing release-state object
- backend/frontend image digests still present in ECR
- an application state suitable for the current database schema
- compatibility with the currently deployed infrastructure

The rollback target is an application release, not an infrastructure version.
Do not roll back infrastructure as part of a normal application rollback.

Do not use an unverified release merely because it is an older Git commit.

### 5.2 Database rule

Rollback is an application-image rollback.

The deployment script runs:

```bash
alembic upgrade head
```

It does not automatically run:

```bash
alembic downgrade
```

Therefore application rollback assumes migration compatibility. Review migration changes between the current release and target release before execution. When a release introduces schema changes that the previous application cannot work with, stop and resolve the database compatibility issue before rollback.

RDS snapshot restore is the last-resort data recovery path; it is not part of the normal application rollback procedure.

### 5.3 Execute the rollback

Use the existing release manifest. Do not build a new image and do not modify CloudFormation or IAM as part of a normal application rollback.

```bash
set -euo pipefail

ROLLBACK_SHA="<previous-release-SHA>"
ROLLBACK_MANIFEST_KEY="manifests/${ROLLBACK_SHA}.json"

DEPLOY_COMMAND="$(
  printf 'exec env TASKFLOW_RELEASE_BUCKET=%q /opt/taskflow/deploy.sh %q' \
    "$RELEASE_BUCKET" \
    "$ROLLBACK_MANIFEST_KEY"
)"

ROLLBACK_SSM_COMMAND_ID=$(
  aws ssm send-command \
    --document-name "AWS-RunShellScript" \
    --instance-ids "$EC2_INSTANCE_ID" \
    --parameters "commands=$DEPLOY_COMMAND" \
    --comment "TaskFlow rollback to ${ROLLBACK_SHA}" \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Command.CommandId' \
    --output text
)

echo "Rollback SSM command ID: $ROLLBACK_SSM_COMMAND_ID"
```

Wait for the SSM command to complete:

```bash
aws ssm wait command-executed \
  --command-id "$ROLLBACK_SSM_COMMAND_ID" \
  --instance-id "$EC2_INSTANCE_ID" \
  --region ap-southeast-1 \
  --profile taskflow
```

Then inspect the completed invocation and confirm the response code:

```bash
aws ssm get-command-invocation \
  --command-id "$ROLLBACK_SSM_COMMAND_ID" \
  --instance-id "$EC2_INSTANCE_ID" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query '{Status:Status,ResponseCode:ResponseCode,Stdout:StandardOutputContent,Stderr:StandardErrorContent}' \
  --output json
```

Expected:

```text
Status = Success
ResponseCode = 0
```

The AWS CLI `command-executed` waiter polls every 5 seconds and stops after 20 unsuccessful checks. A waiter timeout is not, by itself, proof that the deployment command failed; inspect the invocation before deciding whether to stop the procedure.

The `deploy.sh` output should show successful manifest validation, exact image pulls, RDS reachability, migration, backend readiness, proxy readiness, and release-state recording.

### 5.4 Verify the rollback

Confirm the release-state against the target SHA and exact image digests from the manifest:

```bash
set -euo pipefail

ROLLBACK_STATE_FILE="$(mktemp)"
trap 'rm -f "$ROLLBACK_STATE_FILE"' EXIT

aws s3 cp \
  "s3://$RELEASE_BUCKET/release-state/${ROLLBACK_SHA}.json" \
  "$ROLLBACK_STATE_FILE" \
  --region ap-southeast-1 \
  --profile taskflow

BACKEND_DIGEST="$(jq -r '.backend_digest' rollback-manifest.json)"
FRONTEND_DIGEST="$(jq -r '.frontend_digest' rollback-manifest.json)"

BACKEND_ECR_URI=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`BackendEcrRepositoryUri`].OutputValue' \
    --output text
)

FRONTEND_ECR_URI=$(
  aws cloudformation describe-stacks \
    --stack-name taskflow \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendEcrRepositoryUri`].OutputValue' \
    --output text
)

[[ -n "$BACKEND_ECR_URI" && "$BACKEND_ECR_URI" != "None" ]]
[[ -n "$FRONTEND_ECR_URI" && "$FRONTEND_ECR_URI" != "None" ]]

EXPECTED_BACKEND_IMAGE="${BACKEND_ECR_URI}@${BACKEND_DIGEST}"
EXPECTED_FRONTEND_IMAGE="${FRONTEND_ECR_URI}@${FRONTEND_DIGEST}"

jq -e \
  --arg git_sha "$ROLLBACK_SHA" \
  --arg backend_image "$EXPECTED_BACKEND_IMAGE" \
  --arg frontend_image "$EXPECTED_FRONTEND_IMAGE" \
  '
    .git_sha == $git_sha and
    .backend_image == $backend_image and
    .frontend_image == $frontend_image
  ' \
  "$ROLLBACK_STATE_FILE" > /dev/null
```

Verify public service:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' \
  https://app.zctaskflow.athing.cc/

curl -fsS \
  https://api.zctaskflow.athing.cc/api/tasks | jq -r 'type'
```

Expected:

```text
frontend = 200
API = array
```

A successful SSM command alone is not sufficient; the public service and the deployed release-state must also be verified.

## 6. Recovery Procedure

After a rollback rehearsal or incident rollback, recover by deploying the desired release manifest using the same `deploy.sh` path.

Before execution, repeat the rollback preflight checks for `RECOVERY_SHA`: manifest availability and schema validation, manifest SHA match, release-state verification when a prior deployment state exists, ECR digest availability, database compatibility, and infrastructure compatibility.

Example:

```bash
set -euo pipefail

RECOVERY_SHA="<recovery-release-SHA>"
RECOVERY_MANIFEST_KEY="manifests/${RECOVERY_SHA}.json"

DEPLOY_COMMAND="$(
  printf 'exec env TASKFLOW_RELEASE_BUCKET=%q /opt/taskflow/deploy.sh %q' \
    "$RELEASE_BUCKET" \
    "$RECOVERY_MANIFEST_KEY"
)"

RECOVERY_SSM_COMMAND_ID=$(
  aws ssm send-command \
    --document-name "AWS-RunShellScript" \
    --instance-ids "$EC2_INSTANCE_ID" \
    --parameters "commands=$DEPLOY_COMMAND" \
    --comment "TaskFlow recovery to ${RECOVERY_SHA}" \
    --region ap-southeast-1 \
    --profile taskflow \
    --query 'Command.CommandId' \
    --output text
)

echo "Recovery SSM command ID: $RECOVERY_SSM_COMMAND_ID"
```

Wait for the SSM command to complete:

```bash
aws ssm wait command-executed \
  --command-id "$RECOVERY_SSM_COMMAND_ID" \
  --instance-id "$EC2_INSTANCE_ID" \
  --region ap-southeast-1 \
  --profile taskflow
```

Then inspect the completed invocation and confirm the response code:

```bash
aws ssm get-command-invocation \
  --command-id "$RECOVERY_SSM_COMMAND_ID" \
  --instance-id "$EC2_INSTANCE_ID" \
  --region ap-southeast-1 \
  --profile taskflow \
  --query '{Status:Status,ResponseCode:ResponseCode,Stdout:StandardOutputContent,Stderr:StandardErrorContent}' \
  --output json
```

Expected:

```text
Status = Success
ResponseCode = 0
```

The AWS CLI `command-executed` waiter polls every 5 seconds and stops after 20 unsuccessful checks. A waiter timeout is not, by itself, proof that the deployment command failed; inspect the invocation before deciding whether to stop the procedure.

Then perform the same release-state and public smoke checks used for rollback verification.

## 7. Stop-the-Line Conditions

Stop the release, rollback, or recovery procedure and inspect the command output when any of the following occurs:

- selected manifest is missing or malformed
- manifest key does not match `manifest.git_sha`
- exact ECR digest is missing
- SSM command does not complete successfully
- RDS reachability fails
- migration fails
- backend readiness fails
- proxy readiness fails
- release-state does not match the requested SHA and exact image digests
- public frontend smoke test is not HTTP 200
- public API smoke test does not return HTTP 200 with a JSON array
- target application release is incompatible with the current database schema or infrastructure

Do not bypass a failed verification by manually editing S3 release-state.

## 8. Rollback Boundaries

| Layer | Normal release / rollback responsibility |
|---|---|
| Git | Release source identity |
| GitHub Actions | CI gate, release build, manifest, automated deployment, smoke test |
| ECR | Immutable application images |
| S3 | Release manifests and release state |
| SSM | Remote deployment execution |
| EC2 / `deploy.sh` | Runtime deployment and validation |
| RDS | Managed PostgreSQL and persistent data |
| CloudFormation | Stable infrastructure |
| IAM / OIDC | Deployment authorization, not application-release versioning |
| Caddy | Public HTTP/HTTPS entrypoint |

An application rollback does not imply an infrastructure rollback.

## 9. P10 Rollback and Recovery Rehearsal

The P10 rehearsal used a real production deployment target and the existing release artifacts.

### Initial state

Current release:

```text
c04f832b62c17df074e4a1a06e8c13acc3685a03
```

Backend digest:

```text
sha256:65864f472091aefac43ed7a57e7cf6fc56204355ad7d488f124805abf31e2894
```

Frontend digest:

```text
sha256:633133a452cf4835af1cec8b9f1adfebc9cb19adf4cb8b394ec0f991d1ed9418
```

Baseline verification:

```text
frontend -> HTTP 200
/api/tasks -> HTTP 200 + JSON array
```

### Rollback target

```text
38ca2e4ad9f4281f99f2a1f9b0714166e08434f5
```

Backend digest:

```text
sha256:90ae5571573292a3a9b337f0bd195882e7c5d4c4381e3dd31a754f6e9b998028
```

Frontend digest:

```text
sha256:296c379a2f128a720f0f989e636a51709c52de68e1d167e3faff1c6a0c21fdce
```

No Alembic migration files changed between the two release commits.

### Rollback result

The rollback was executed through SSM against the existing EC2 instance using:

```text
manifests/38ca2e4ad9f4281f99f2a1f9b0714166e08434f5.json
```

Result:

```text
SSM Status    = Success
ResponseCode  = 0
```

The deployment script completed through:

```text
RDS reachability
database migration
backend readiness
frontend update
proxy readiness
release-state recording
```

Post-rollback verification:

```text
release-state.git_sha = 38ca2e4...
frontend               = HTTP 200
/api/tasks             = HTTP 200 + JSON array
```

### Rehearsal evidence

Rollback SSM command:

```text
3f4509e1-ee83-448e-a27e-6e53fc5d1ca9
```

Recovery SSM command:

```text
fefa619a-1e3c-4370-b965-5b9631c751b3
```

Historical P9 deployment runs:

```text
38ca2e4 -> GitHub Deploy run 36450605771 (post-deploy verification failure)
c04f832 -> GitHub Deploy run 36456229892 (success)
```

### Recovery result

Recovery was then executed with:

```text
manifests/c04f832b62c17df074e4a1a06e8c13acc3685a03.json
```

Result:

```text
SSM Status    = Success
ResponseCode  = 0
```

The final release-state returned to:

```text
c04f832b62c17df074e4a1a06e8c13acc3685a03
```

Final public verification:

```text
frontend               = HTTP 200
/api/tasks             = HTTP 200 + JSON array
```

This rehearsal demonstrated the complete path:

```text
current release
-> previous release
-> external verification
-> recovery to current release
-> external verification
```

## 10. Historical Verification Note

Release `38ca2e4` was previously deployed by the P9 workflow. The historical GitHub Deploy run failed during the post-deploy release-state read with S3 `HeadObject` HTTP 403 after the SSM deployment had already completed successfully.

The missing `s3:GetObject` permission was subsequently added to the `taskflow-github-deploy` role. This historical workflow failure does not mean that the application deployment itself failed, and it does not make the old IAM policy part of an application rollback.

## 11. Public Endpoints

Frontend:

```text
https://app.zctaskflow.athing.cc/
```

Backend API:

```text
https://api.zctaskflow.athing.cc/
```

API documentation:

```text
https://api.zctaskflow.athing.cc/docs
```
