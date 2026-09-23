# AGENTS.md — TaskFlow Module 3 (`module-3/`)

Operating rules for coding agents working in this directory. Read this file before
making any change.

## Authoritative documents (in order)

1. `docs/product-spec.md` — the finalized Product Specification (v1.3). Authoritative
   for scope and requirements. Do not edit it to make a change fit; if your task
   conflicts with it, stop and flag.
2. `implementation-plan.md` — the phase roadmap, file map, and TBD register.
3. The finalized AWS architecture decisions as embedded in the implementation plan
   (Phases 7–10) and, once created, `docs/deployment.md`. Open `TBD` items in the plan
   remain open decisions and must not be silently promoted to project requirements.

## Non-negotiable constraints

### Product scope
- The finalized Product Spec is authoritative. Do not reinterpret it.
- Do not add authentication. No users, login, JWT/session handling, roles, ownership,
  or authorization. Authentication is N/A for the current unauthenticated TaskFlow
  MVP.
- Do not add separate staging/production environments, promotion workflows, extra
  environment URLs, per-environment builds, or environment-parity architecture in
  Module 3. The scope does not prescribe separate staging/production environments.
- Do not expand TaskFlow product functionality.
- Preserve TaskFlow CRUD behavior and the existing API contract.
- Preserve the `TaskRepository` abstraction (in-memory + SQLAlchemy implementations).

### Database and migrations
- PostgreSQL is the deployed runtime database.
- Alembic is the schema authority.
- Never use `Base.metadata.create_all()` in production/deployment paths. Integration
  tests set up schema via the Alembic chain; unit tests use the in-memory repository.
- Never run Alembic automatically during FastAPI startup.
- Migration is explicit and gated: `alembic upgrade head` runs as a separate one-off
  step before the backend update; deployment stops immediately if migration fails.
- In Module 3, use one dedicated `taskflow` PostgreSQL user for both backend runtime and
  Alembic. The RDS master/admin credential is for one-time privileged bootstrap only and
  must never become the long-term application credential. Separate runtime and migration
  users are future hardening for Module 4+ and are out of scope here.
- No automatic `alembic downgrade` as the default rollback mechanism. Prefer
  backward-compatible migrations so application image rollback stays feasible.
- The PostgreSQL enum for task status is named `task_status` with exactly
  `todo`, `in_progress`, `done`.

### Frontend and routing
- The frontend is a separate Nitro `node-server` container
  (`node .output/server/index.mjs`, internal port 3000). No Cloudflare/Wrangler
  runtime.
- Direct browser → backend API origin is required. No same-origin `/api` proxy, no
  reverse-proxy layer in the frontend.
- No SSR/server-function data-fetching redesign. The client-side TanStack Query flow
  is preserved.
- `VITE_API_BASE_URL` is build-time, browser-visible, and non-secret. Do not add a
  runtime configuration injection mechanism.

### Configuration and secrets
- `DATABASE_URL` is runtime-only and secret. On EC2 it is constructed at runtime from
  SSM Parameter Store SecureString values. It must never appear in Git, image
  layers, logs, CloudFormation outputs, or GitHub.
- Initial TaskFlow runtime DB credentials are bootstrapped manually with
  `aws ssm put-parameter --type SecureString` (or the equivalent secure AWS CLI form).
  Do not pass secret values through CloudFormation, commit them to source, or expose
  them to GitHub Actions.
- The RDS master/admin credential is a one-time provisioning/bootstrap credential used
  only to create the dedicated `taskflow` user. Its acquisition and temporary-storage
  mechanism must be explicitly documented and approved before P7/P8 execution. Never
  use the master/admin credential as the runtime application credential or `DATABASE_URL`.
- CORS uses exact origins via `CORS_ALLOWED_ORIGINS`. No wildcard origins.
- RDS remains private (reachable only from the EC2 application security group on
  5432).
- Frontend/backend application ports are not directly exposed publicly; only 80/443
  via Caddy.

### AWS and deployment
- Region: `ap-southeast-1`. Platform baseline: EC2 + Docker Compose, Amazon ECR,
  Amazon RDS for PostgreSQL, AWS CloudFormation, GitHub Actions, SSM Run Command,
  Caddy with ACME TLS.
- CI/CD uses GitHub OIDC and short-lived AWS credentials. No long-lived AWS keys in
  GitHub.
- Deployment is gated on successful required CI checks for the **same commit SHA** on
  `main`; do not deploy from pull requests. The preferred `workflow_run` design must
  require `conclusion == success`, a CI push event to `main`, and deployment of that
  exact `workflow_run.head_sha` (or an equivalent explicit same-SHA gate).
- EC2 deployment uses SSM Run Command, not CI SSH.
- Application images deploy by immutable ECR digest.
- CloudFormation manages stable infrastructure only — it is not the normal
  application-release mechanism. The selected SSM release-manifest/deployment-bundle
  design uses a versioned S3 artifact bucket; this is an implementation mechanism, not
  a separate Module 3 product requirement.
- Preserve the release sequence: merge to main → CI gate → OIDC → build → ECR push →
  resolve digests → (infra update only if infra changed) → release manifest → SSM
  Run Command → pull digests → retrieve secrets → verify RDS → `alembic upgrade head`
  (stop on failure) → update backend → verify readiness → update frontend → verify
  proxy → public smoke test → record release state.
- Backend readiness contract: internal `GET /api/tasks` must return HTTP 200 with a
  valid JSON array after the backend update. Do not add a new health endpoint.
- Do not require `create_app()` itself to establish live PostgreSQL connectivity.
  Database connectivity and schema validity are verified by Alembic, integration tests,
  and deployment readiness/reachability gates.

### Repository hygiene
- Never commit secrets, `.env` files, credentials, generated database files, or
  runtime database artifacts.
- All Module 3 artifacts stay under `module-3/`, except GitHub Actions workflows,
  which live at the repository root `.github/workflows/` and operate on `module-3/`.

## Agent behavior rules

- Do not make unrelated refactors.
- Do not expand scope.
- Do not silently change locked architecture decisions.
- Prefer small, verifiable changes.
- Run focused tests first, then the broader required validation.
- Do not invent repository files, functions, endpoints, tests, or infrastructure.
  If evidence is insufficient, mark the item `NEEDS VERIFICATION` or `TBD` (see the
  TBD register in `implementation-plan.md`).
- Follow the current phase in `implementation-plan.md`; do not skip gates. Treat any
  item marked `TBD`, `Open implementation detail`, or `NEEDS VERIFICATION` as unresolved
  until explicitly decided or verified; do not invent a decision merely to unblock
  implementation.
- Stop and flag a conflict when the requested change contradicts the Product Spec or
  this file — do not work around it.

## Required checks before declaring work complete

Run what applies to your change, focused first:

```bash
# Backend (from module-3/backend)
uv run pytest                      # unit tier (in-memory repository; no DB)

# Integration (from module-3; requires a reachable PostgreSQL and TEST_DATABASE_URL)
#   exact invocation: see implementation-plan.md Phase 3

# Frontend (from module-3/frontend)
bun run test                       # script name: verify against package.json
bun run build                      # must produce .output/server/index.mjs (Nitro node-server)

# Local stack (from module-3)
docker compose up -d --build
curl -fsS http://localhost:3000/
curl -fsS http://localhost:8000/api/tasks
```

For deployment-path changes also confirm: migration runs before backend update and
the script stops on migration failure; readiness poll requires 200 + JSON array;
no secrets in logs, images, or CloudFormation outputs.

## Documentation you must update

When architecture or deployment behavior changes, update the relevant document:
`docs/testing.md`, `docs/deployment.md` (once created — do not create it before its
planned phase), `docs/release-process.md`, or `README.md`. Do not modify
`docs/product-spec.md`; flag needed spec changes instead.
