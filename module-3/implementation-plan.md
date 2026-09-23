# TaskFlow — Module 3 Implementation Plan

**Version:** 1.3 (revised draft for final review — pre-coding-phase baseline)
**Based on:** `module-3/docs/product-spec.md` (finalized v1.3) and the finalized AWS
architecture / remaining-implementation-inputs decision record (Terra).
**Git baseline:** `b1c758c — docs(m3): finalize TaskFlow product specification`
**Status:** Planning only. No code, no CloudFormation, no Dockerfiles, no workflow YAML,
and no `docs/deployment.md` are produced by this document. Core architecture and the
pre-P7 implementation decisions are locked; remaining TBDs are explicitly tracked.

---

## 0. Conventions, Sources, and Boundaries

### 0.1 Path conventions

- All paths are relative to `module-3/` unless explicitly rooted at the repository root.
- Repository root is `ai-dev-tools-zoomcamp/` (contains `module-2/`, `module-3/`).
- GitHub Actions workflows live at the repository root `.github/workflows/` (GitHub
  discovers workflows only from the repository root). Workflows operate on `module-3/`
  via `working-directory` and path filters on `module-3/**`.
- Paths under `module-3/deploy/` and `module-3/infra/` are **proposed** locations for
  new artifacts (no existing evidence fixes them); they are marked [proposed] and may be
  adjusted at implementation kickoff without changing any decision in this plan.

### 0.2 Authoritative inputs (priority order)

1. `module-3/docs/product-spec.md` — finalized v1.3 (do not modify; changes go through
   its own change process).
2. Finalized AWS architecture / implementation-input decisions (region, EC2, Compose,
   ECR, RDS, CloudFormation, OIDC, SSM, Caddy/ACME, secret store, readiness contract).
3. Existing Module 2 / current-codebase evidence (conversation context).
4. General engineering best practice — never overrides 1–3.

### 0.3 Deployment responsibility boundaries (preserved)

| Layer | Owns |
|---|---|
| CloudFormation | Stable AWS infrastructure only. **Not** the normal application-release mechanism. |
| GitHub Actions | CI, image build, ECR push, conditional infra update, release manifest, SSM deployment trigger, public smoke test |
| EC2 | Docker Compose runtime and the controlled deployment script |
| ECR | Immutable application images (referenced by digest) |
| RDS | Managed PostgreSQL (private) |
| SSM | Executes the deployment operation on EC2 (Run Command) + Parameter Store secrets |

### 0.4 Release sequence (normative — must be preserved end to end)

```
merge to main
→ required CI checks pass
→ GitHub OIDC authentication
→ build frontend/backend images
→ push immutable images to ECR
→ resolve image digests
→ update CloudFormation only when infrastructure changes
→ create/upload release manifest
→ invoke SSM Run Command
→ EC2 pulls exact image digests
→ retrieve runtime secrets
→ verify RDS reachability
→ run `alembic upgrade head`
→ stop immediately if migration fails
→ update backend
→ verify backend readiness
→ update frontend
→ verify local/proxy readiness
→ run public smoke test
→ record deployed image digests / release state
```

**Migration safety (locked):** explicit one-off migration; no production
`create_all()`; no Alembic from application startup; no automatic
`alembic downgrade` as the default rollback mechanism; prefer
backward-compatible migrations so application image rollback remains possible
where feasible.

### 0.5 Backend readiness contract (locked)

After the backend container is updated, the deployment script considers the backend
ready only when:

```
GET http://backend:8000/api/tasks  →  HTTP 200 + valid JSON array
```

(internal Compose-network request). This verifies process, routing, repository,
PostgreSQL connectivity, and migrated schema. **Do not add a new health endpoint.**

### 0.6 Compose topologies (two distinct files)

| Stack | Services | Notes |
|---|---|---|
| Local dev (`module-3/docker-compose.yml`) | `postgres` → `migrate` → `backend` → `frontend` | Locked ordering (spec A-7); local config contract (§3.5). |
| EC2 runtime (proposed `module-3/deploy/compose/…`) | `caddy`, `backend`, `frontend` (+ run-once `migrate`) | PostgreSQL is RDS (external, private); migration is a one-off step invoked by the deployment script before backend update; only 80/443 are published. |

This is consistent with spec A-7 ("migration runs as a separate Compose step **and**
as a deploy-time step in CD") — see Review Summary, Interpretation Note 1.

### 0.7 Prerequisites and deployment-time user inputs

| # | Input | Required before |
|---|---|---|
| U1 | Base domain (real domain to use) | P8/P9 public HTTPS and frontend build value |
| U2 | DNS ownership: Route 53 hosted zone ID **or** external DNS provider confirmation | P8 Caddy/ACME DNS setup |
| U3 | ACME contact email (Caddy) | P8 Caddy/ACME setup |
| U4 | Initial DB credentials via the approved manual SSM bootstrap path (never Git/chat) | P8 application deployment / runtime secret assembly |
| U5 | Cost approval: EC2, RDS, EBS, public IPv4, ECR, retained snapshots | P7 actual AWS provisioning |
| U6 | RDS preflight: confirm `db.t4g.micro` + PostgreSQL 16 orderable in `ap-southeast-1` for the account (or authorize smallest compatible alternative) | P7 actual RDS provisioning |

---

### 0.8 Pre-implementation decision gates

The following are implementation choices that must be resolved before the phases that depend on them. They do not reopen product scope or the locked core architecture.

| Decision | Gate | Current direction |
|---|---|---|
| Runtime secret bootstrap | Before P8 | **Locked:** perform a one-time/manual `aws ssm put-parameter --type SecureString` bootstrap for TaskFlow runtime credentials. Do not place secret values in CloudFormation outputs, source, or GitHub Actions. |
| Dedicated DB user bootstrap | Before P8 | **Locked:** use the RDS master/admin credential only for a one-time privileged bootstrap that creates the dedicated `taskflow` DB user. In Module 3, the same `taskflow` user is used by both backend runtime and Alembic. Do not use the RDS master credential as the long-term application credential. The acquisition and temporary-storage mechanism for the master/admin credential must be explicitly documented before P7/P8 execution. |
| Deploy gating | Before P9 | **Locked:** deployment runs only after required CI checks succeed for the same commit SHA on `main`; do not deploy from pull requests. Preferred workflow mechanism: a successful CI `workflow_run` starts `deploy.yml` for that same SHA. |
| CloudFormation conditional update | Before P9 | Detect whether `module-3/infra/**` changed in the release commit/range and run CloudFormation only when needed. Exact shell/implementation mechanism remains a P9 implementation detail and is not yet locked. |

These gates are intentionally separated from user-provided deployment inputs U1–U6. The implementation plan may be reviewed and committed before the real domain or database credentials are available.

## 1. Phase Map (20 required areas → phases)

| # | Required area | Phase |
|---|---|---|
| 1 | Current baseline / starting state | P0 |
| 2 | PostgreSQL runtime transition | P1 |
| 3 | Alembic integration | P2 |
| 4 | Real PostgreSQL integration tests | P3 |
| 5 | Dockerfile / containerization | P4 |
| 6 | Docker Compose | P5 |
| 7 | CI workflow | P6 |
| 8 | CloudFormation infrastructure | P7 |
| 9 | ECR setup | P7 (creation) / P9 (push + digests) |
| 10 | EC2 bootstrap/configuration | P8 |
| 11 | SSM deployment | P8 (script) / P9 (trigger) |
| 12 | Caddy + ACME | P8 |
| 13 | Runtime secrets/configuration | P7 (creation) / P8 (retrieval + assembly) |
| 14 | Merge-to-main deployment | P9 |
| 15 | Migration gating | P8 (enforcement) / P9 (ordering) |
| 16 | Backend readiness | P8 |
| 17 | Public smoke test | P9 |
| 18 | Rollback procedure/documentation | P10 |
| 19 | Final documentation updates | P11 |
| 20 | Final verification / acceptance gate | P12 |

Branch discipline: one branch + PR per phase (`m3/<phase-topic>`), merged through CI
once CI exists (P6). Phases P1–P5 land before CI; their first CI validation occurs
when P6 introduces the workflow.

---

## Phase 0 — Baseline Verification and Prerequisites

**Objective.** Confirm the starting state is green, establish branch discipline, and
surface deployment-time user inputs and preflights before AWS/deployment work begins.

**Dependencies.** Git baseline `b1c758c`.

**Files.** None created or modified (this phase changes no repository content).

**Key tasks.**
- Record the current baseline test results (observed baseline: 77 backend tests and 8 frontend tests passing; verify at kickoff; counts may increase as new tests are added).
- Create the working branch (`m3/implementation` or per-phase branches).
- Check `.gitignore` coverage for `backend/data/`, `.env*`, `node_modules/`,
  `.output/`, and any runtime DB artifacts (NEEDS VERIFICATION: current ignore rules).
- Collect and track user inputs U1–U6 (§0.7). Do not block all implementation on U1–U3; those inputs gate only the affected DNS/TLS/public-deployment work.
- Resolve U5/U6 before actual AWS infrastructure provisioning in P7; resolve U4 before the application is deployed with runtime database credentials.
- Confirm the Nitro POC branch reference (`m3-poc/frontend-node-server` @ `af3b594`)
  is available for incorporation in P4.

**Verification.**
```bash
cd module-3/backend  && uv run pytest          # verify current baseline; initially 77 passed
cd module-3/frontend && bun run test            # verify current baseline; initially 8 passed
```

**Expected result.** Documented green baseline; prerequisites tracked.

**Gate.** Both suites green on the working branch; branch created; U1–U6 captured with unresolved items explicitly tracked for the phases they block. P7 is not blocked by U1–U3, while P7 provisioning remains gated by U5/U6.

---

## Phase 1 — PostgreSQL Runtime Transition (Backend)

**Objective.** The backend runs against PostgreSQL via `DATABASE_URL`, with explicit
failure modes, environment-driven CORS, no SQLite runtime default, and no
`create_all()` in the runtime path.

**Dependencies.** P0.

**Files.**

| Path | Action | Type |
|---|---|---|
| `backend/taskflow_backend/app.py` | Modify | Code |
| `backend/taskflow_backend/repositories/sqlalchemy.py` | Modify | Code |
| `backend/taskflow_backend/db/base.py` | New | Code |
| `backend/taskflow_backend/db/models.py` | New | Code |
| `backend/taskflow_backend/db/__init__.py` | New/verify (package exists but holds no ORM) | Code |
| `backend/pyproject.toml`, `backend/uv.lock` | Modify (add `psycopg[binary]`) | Code |
| `backend/tests/test_sqlalchemy_repository.py`, `backend/tests/test_sqlite_api.py`, `backend/tests/conftest.py` | Modify / supersede | Code |

**Key tasks.**
- Re-home `Base` → `db/base.py` and the ORM model → `db/models.py` (locked
  architecture-review direction; required so Alembic's target metadata can import them
  in P2). Repository imports from the new modules.
- `SqlAlchemyTaskRepository`: constructor accepts a **database URL** (not a SQLite
  file path); remove `Base.metadata.create_all()` from construction; preserve
  session-per-operation, `expire_on_commit=False`, UTC normalization, and CRUD/mapping
  behavior.
- `app.py`: when no repository is injected, construct from `DATABASE_URL`
  (`postgresql+psycopg://…`). Remove the SQLite default (`backend/data/taskflow.db`).
  Missing/malformed `DATABASE_URL` → explicit configuration/startup failure; no silent
  SQLite fallback. Database connectivity is **not** required to be established by
  `create_app()` itself; connectivity is verified by Alembic, integration tests, and the
  deployment readiness/reachability gates in later phases.
- CORS: read exact origins from `CORS_ALLOWED_ORIGINS` (comma-separated), no wildcard,
  `allow_credentials=False`; replaces the hardcoded `http://localhost:5173`.
  Decide and document unset-`CORS_ALLOWED_ORIGINS` behavior (recommend explicit
  failure, consistent with `DATABASE_URL`).
- Add `psycopg` driver dependency (canonical URL format implies psycopg).
- Unit-test tier: keep in-memory-repository tests DB-free (spec AC-3.1). SQLite-file
  tests are **superseded** by the P3 PostgreSQL integration suite — port their coverage
  forward; optionally retain a slim SQLite/Alembic cross-check (implementation
  decision). SQLite must never substitute for the P3 integration coverage.

**Verification.**
```bash
cd module-3/backend && uv run pytest
DATABASE_URL= uv run python -c "from taskflow_backend.app import create_app; create_app()"   # expect explicit config failure
DATABASE_URL="not-a-url" …                                                                    # expect explicit config failure
# Do not require create_app() itself to prove live PostgreSQL connectivity; connection
# and schema checks are covered by P2/P3/P8.
```
Add unit tests asserting the failure modes (monkeypatched env).

**Expected result.** Unit suite green including new config-failure tests; no
`create_all()` call remains in `app.py`/repository runtime path; SQLite default gone.

**Gate.** All of the above; no behavior change to API contract (P0 tests still pass
where retained).

---

## Phase 2 — Alembic Integration

**Objective.** Alembic is the schema authority: a migration chain that creates the
current schema (tasks table + `task_status` enum) from an empty PostgreSQL database.

**Dependencies.** P1 (models importable from `db/`).

**Files.**

| Path | Action | Type |
|---|---|---|
| `backend/alembic.ini` | New | Code |
| `backend/alembic/env.py` | New | Code |
| `backend/alembic/script.py.mako` | New (generated by init) | Code |
| `backend/alembic/versions/<rev>_create_tasks_and_task_status.py` | New | Code |
| `backend/pyproject.toml`, `backend/uv.lock` | Modify (add `alembic`) | Code |

**Key tasks.**
- `env.py`: target metadata imports `db.base.Base` + `db.models`; database URL taken
  from the environment (variable naming is an implementation decision; must fail
  explicitly when absent/unusable).
- Initial revision creates: native PostgreSQL enum **`task_status`** with exactly
  `todo`, `in_progress`, `done`; `tasks` table preserving the baseline logical contract
  (id PK autoincrement; title NOT NULL; description NOT NULL default `''`; status
  enum NOT NULL; `created_at`/`updated_at` timezone-aware, `updated_at` advances on
  update — app-managed timestamps preserved).
- Domain/API status values unchanged (spec A-8, FR-level baseline).

**Verification.**
```bash
docker run -d --name tf-scratch -e POSTGRES_PASSWORD=scratch -e POSTGRES_DB=taskflow \
  -p 127.0.0.1:55001:5432 postgres:16
cd module-3/backend
DATABASE_URL="postgresql+psycopg://postgres:scratch@127.0.0.1:55001/taskflow" uv run alembic upgrade head
docker exec -it tf-scratch psql -U postgres -d taskflow -c '\d tasks' -c '\dT task_status'
# dev-only sanity (NOT the production rollback path):
DATABASE_URL=… uv run alembic downgrade base && DATABASE_URL=… uv run alembic upgrade head
```

**Expected result.** Fresh empty DB → `upgrade head` → schema matches the baseline
contract; enum exists with exact values.

**Gate.** AC-2.1 satisfied; downgrade/upgrade cycle verified in the scratch DB only.

---

## Phase 3 — Real PostgreSQL Integration Tests (+ Frontend-to-Backend Flow)

**Objective.** Integration suite under `module-3/tests/integration/` running against a
real PostgreSQL via `TEST_DATABASE_URL`, using the Alembic chain; plus the
frontend-to-backend flow test.

**Dependencies.** P2.

**Files.**

| Path | Action | Type |
|---|---|---|
| `tests/integration/` (backend PG suite: `conftest.py`, test modules) | New | Code |
| `tests/integration/f2b/` (frontend-to-backend suite) | New | Code |
| pytest import-path config (make `taskflow_backend` importable from `tests/integration/`) | New — mechanism TBD | Code |
| Local test-PostgreSQL helper (documented `docker run` or small script) | New | Code |

**Key tasks.**
- Fixture lifecycle (locked): `TEST_DATABASE_URL` → PostgreSQL reachable (fail loudly,
  never silently skip/pass) → `alembic upgrade head` → clear task data between tests →
  repository → `create_app(repo=…)` → tests. Never `create_all()` in this suite.
- The test database itself is expected to exist (created by container env
  `POSTGRES_DB=…` locally / CI service container; RDS creates `taskflow` via
  CloudFormation). Alembic creates the schema, not the database.
- Coverage (ports the superseded SQLite tests forward): list (incl. empty), create,
  partial update, status change, delete, missing-resource behavior; timezone-aware
  UTC timestamps; `updated_at` advances on update.
- F2B test (spec AC-3.5): the real frontend API client ↔ real backend ↔ real
  PostgreSQL, exercising the configured API path. Tooling is open (options: Playwright
  against the full stack, or a Node-side test driving the actual client); selection is an
  implementation decision recorded when built. **If the test is intended to verify
  browser-enforced CORS behavior specifically, use a browser-based test such as
  Playwright; a Node-side HTTP client does not itself enforce browser CORS rules.**
- Keep the suite fast enough for every push (spec R-intent; working target
  single-digit minutes).

**Verification.**
```bash
docker run -d --name tf-test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_DB=taskflow_test \
  -p 127.0.0.1:55002:5432 postgres:16
cd module-3 && TEST_DATABASE_URL="postgresql+psycopg://postgres:test@127.0.0.1:55002/taskflow_test" \
  <pytest invocation for tests/integration/>      # exact invocation: VERIFY (import-path mechanism)
# Negative check: stop the container → suite must FAIL with a clear diagnostic
```

**Expected result.** Suite green against real PostgreSQL; loud failure when
PostgreSQL is unreachable; F2B test exercises a full task lifecycle through the real
frontend/API path. If browser-enforced CORS is included in the chosen F2B test, that
behavior is explicitly verified by the selected browser-based tooling.

**Gate.** AC-3.2/3.3/3.5 satisfied; no `create_all()` anywhere in the integration
path.

---

## Phase 4 — Container Images

**Objective.** Reproducible multi-stage images: backend (FastAPI/Uvicorn, port 8000)
and frontend (Nitro `node-server`, port 3000), with the preset override **verified in a
real build** (spec OD-4).

**Dependencies.** P1, P2 (backend image must contain Alembic + models for the
migration step).

**Files.**

| Path | Action | Type |
|---|---|---|
| `backend/Dockerfile` | New (per-service organization recommended; a single multi-target Dockerfile is equally valid per spec AC-4.1 — implementation decision) | Infra |
| `frontend/Dockerfile` | New | Infra |
| `frontend/vite.config.ts` | Modify (incorporate POC `af3b594`: Nitro `node-server` preset; preserve custom `src/server.ts` entry) | Code |

**Key tasks.**
- Backend: multi-stage; uv-based dependency install from `pyproject.toml`/`uv.lock`;
  includes Alembic + migration chain; non-root runtime user; listens on 8000.
  Entry command (e.g., `uvicorn taskflow_backend.app:create_app --factory`) — exact
  invocation: VERIFY.
- Frontend: multi-stage; build stage runs the real build (`bun run build` — verified
  in POC) with `VITE_API_BASE_URL` supplied as a build arg; runtime stage runs
  `node .output/server/index.mjs` on 3000; Node base image version must satisfy the
  project's engine constraints (spec A-9) — version: VERIFY against `package.json`.
- **OD-4 verification (gate item):** after a real build, confirm
  `.output/server/index.mjs` exists, `nitro.json` reports `preset: node-server`, and no
  `wrangler.json`/Cloudflare artifacts are produced.
- No secrets, no `.env`, no database files in image layers.

**Verification.**
```bash
cd module-3/frontend && bun run build   # then inspect .output/nitro.json, absence of wrangler.json
docker build -t taskflow-backend  module-3/backend
docker build --build-arg VITE_API_BASE_URL=http://localhost:8000 -t taskflow-frontend module-3/frontend
docker run --rm -d -p 3000:3000 taskflow-frontend && curl -fsS http://localhost:3000/
docker run --rm taskflow-backend   # without DATABASE_URL → must fail explicitly
```

**Expected result.** Both images build and behave; backend fails explicitly without
config.

**Gate.** Images build reproducibly; OD-4 closed (preset honored in a real build);
AC-4.1/4.2 satisfied.

---

## Phase 5 — Docker Compose (Local Stack)

**Objective.** One-command local application with the locked topology and
configuration contract.

**Dependencies.** P2, P4.

**Files.**

| Path | Action | Type |
|---|---|---|
| `docker-compose.yml` | New | Infra |
| `README.md` | Modify (initial local-setup section; final polish in P11) | Docs |

**Key tasks.**
- Services: `postgres` (image `postgres:16` — major version aligned with RDS;
  healthcheck; persistent volume; no published host port by default), `migrate`
  (backend image; command `alembic upgrade head`; `depends_on` postgres healthy;
  recommended implementation: reuse the backend image with an alternate command),
  `backend` (`depends_on` migrate `service_completed_successfully`; port 8000),
  `frontend` (build arg `VITE_API_BASE_URL=http://localhost:8000`; port 3000).
- Locked local config contract (exact):
  - `DATABASE_URL=postgresql+psycopg://taskflow:taskflow@postgres:5432/taskflow`
  - `VITE_API_BASE_URL=http://localhost:8000`
  - `CORS_ALLOWED_ORIGINS=http://localhost:3000`
  - Forbidden: `VITE_API_BASE_URL=http://backend:8000`.
- Data survives `docker compose down && up` (volume).

**Verification.**
```bash
git clone <repo> && cd ai-dev-tools-zoomcamp/module-3 && docker compose up -d --build
docker compose ps                       # postgres healthy → migrate exited 0 → backend/frontend up
curl -fsS http://localhost:3000/        # frontend served
curl -fsS http://localhost:8000/api/tasks   # JSON array
# browser CRUD: create → edit → status change → delete
docker compose down && docker compose up -d && curl -fsS http://localhost:8000/api/tasks  # data persisted
```

**Expected result.** Working local stack from a clean clone (spec AC-4.3/4.4).

**Gate.** Reproducibility verified on a clean clone; ordering observed; persistence
verified.

---

## Phase 6 — CI Workflow

**Objective.** Every push/PR to `module-3/**`: lint, unit, integration (real
PostgreSQL service), container build; PRs gated.

**Dependencies.** P3, P4 (CI runs what exists), P5.

**Files.**

| Path | Action | Type |
|---|---|---|
| `.github/workflows/ci.yml` (repository root) | New | CI |

> Naming note: the finalized Product Spec §8 lists `.github/workflows/ci.yml` /
> `.github/workflows/deploy.yml`; this plan uses those names. Because the repository
> hosts multiple modules, confirm at kickoff whether module-scoped filenames
> (e.g., `module-3-ci.yml`) are preferred — a naming choice only, not an
> architecture change. Either way the workflow must operate on `module-3/` paths.

**Key tasks.**
- Triggers: push + pull_request, path-filtered to `module-3/**` (and the workflow file).
- Jobs: backend lint + unit; frontend lint + unit; integration — `postgres:16` service
  container with health options, wait for readiness, `alembic upgrade head` with
  `TEST_DATABASE_URL`, then the integration suite + F2B suite; container build job
  (build both images; no push, no AWS credentials needed in CI).
- Lint tooling: confirm existing setup first (backend ruff? frontend eslint config?)
  — NEEDS VERIFICATION; select minimal tooling if absent (implementation decision).
- Branch protection: configure required checks (repo-admin action; document in P10).

**Verification.**
```bash
# open a PR touching module-3/** → all checks run and pass
# push a deliberately failing test → merge is blocked
```

**Expected result.** Spec AC-5.1/5.2 satisfied.

**Gate.** CI green on a real PR; a failing check blocks merge.

---

## Phase 7 — CloudFormation Infrastructure (incl. ECR, Secrets, S3)

**Objective.** Stable AWS infrastructure, reproducible via one stack; all finalized
baselines applied.

**Dependencies.** P0, P5/P6 ideally merged (infra is code-independent but
should land on a green main). Actual AWS provisioning is gated by U5/U6; U1–U3 are
not required to create the core VPC/EC2/RDS/ECR infrastructure.

**Files.**

| Path | Action | Type |
|---|---|---|
| `infra/cloudformation/taskflow.yaml` [proposed] | New | Infra |

**Key tasks.**
- Preflights (before stack creation; account/time-dependent — run, don't assume):
  ```bash
  aws rds describe-db-engine-versions --engine postgres --region ap-southeast-1 \
    --query 'DBEngineVersions[].EngineVersion'            # confirm PG16 + db.t4g.micro orderability path
  # resolve current AL2023 x86_64 AMI via SSM public parameter (exact path: VERIFY vs current AWS docs)
  # confirm t3.small availability and acceptable pricing in ap-southeast-1
  ```
- Resources: dedicated VPC (`10.42.0.0/16` default param), IGW, one public subnet
  (AZ-A) + public route table, two private DB subnets (distinct AZs) + private route
  table, EC2 app SG (inbound 80/443), RDS SG (5432 from EC2 SG only); EC2 `t3.small`
  AL2023 x86_64, 20 GiB encrypted gp3 root, Elastic IP + association; IAM EC2 instance
  profile (SSM managed-instance core, ECR pull, `ssm:GetParameter(s)` on
  `/taskflow/*`, S3 artifact read, S3 release-state write); GitHub OIDC provider +
  scoped deployment role (ECR push, SSM Send Command + status read, S3 manifest
  write, CloudFormation deploy incl. scoped `iam:PassRole` for the instance profile —
  exact policy statements: implementation detail of this phase); RDS PostgreSQL 16
  (`db.t4g.micro` default param), private, single-AZ, encrypted, gp3 20 GiB →
  autoscale 50 GiB, 1-day backups, snapshot-on-delete/replace, DB subnet group, DB
  name `taskflow`; ECR repositories (frontend, backend) + lifecycle policies; **S3
  release-artifact bucket (+ lifecycle) is required for the selected SSM release-manifest
  and deployment-bundle design, but is not a Module 3 course requirement**; CloudWatch
  log group for SSM output; instance tags for Run Command targeting.
- Secrets: SSM Parameter Store SecureString at `/taskflow/database/username`,
  `/taskflow/database/password`, `/taskflow/database/name` (+ String
  `/taskflow/caddy/acme-email`). **Locked bootstrap:** populate the runtime secret
  values one time using manual `aws ssm put-parameter` commands. CloudFormation must
  not receive, store, or output the secret values.
- Database-user strategy: **locked for Module 3:** use the RDS master/admin credential
  only for a one-time privileged bootstrap that creates the dedicated `taskflow` user.
  The `taskflow` user is used by both backend runtime and Alembic in this module. The
  master credential is never the long-term application credential. Separate runtime and
  migration users are future hardening for Module 4+ and are out of scope here. The
  bootstrap is a one-time operational action, not part of the routine release workflow.
  **Master/admin credential handling:** its acquisition and temporary-storage mechanism
  must be explicitly documented and approved before P7/P8 execution; it must never be
  committed to Git, passed through routine GitHub Actions deployment, written to the
  runtime application environment, or used as the application `DATABASE_URL`.
- Outputs (non-secret only): Elastic IP, RDS endpoint, ECR repository URIs, SSM
  parameter names, S3 bucket, CloudWatch log group.
- DNS: if U2 confirms a Route 53 hosted zone owned by CloudFormation, create the two
  `A` records there. Otherwise leave DNS creation to the external provider using the
  Elastic IP output. DNS is not a prerequisite for the rest of the core stack.

**Verification.**
```bash
aws cloudformation deploy --template-file module-3/infra/cloudformation/taskflow.yaml \
  --stack-name taskflow --region ap-southeast-1 --capabilities CAPABILITY_NAMED_IAM …
aws cloudformation describe-stacks --stack-name taskflow --query 'Stacks[0].StackStatus'   # CREATE_COMPLETE
# verify: RDS PubliclyAccessible=false; SG rules as specified; ECR repos exist; no secret outputs
```

**Expected result.** Stack complete; EIP/RDS endpoint/ECR URIs available as outputs;
RDS private.

**Gate.** `CREATE_COMPLETE`; U5/U6 preflights recorded and passed; required core
resources are healthy and outputs are available. U1–U3 may remain unresolved until the
P8/P9 public HTTPS work; U4 must be resolved before application runtime credentials are
assembled and the deployed service is started against RDS.

---

## Phase 8 — EC2 Bootstrap, Caddy + ACME, Deployment Script, Runtime Secrets

**Objective.** The EC2 host runs the Compose runtime behind Caddy; the controlled
deployment script implements the locked release sequence; secrets retrieved and
assembled at runtime only.

**Dependencies.** P4 (images), P7 (infra).

**Files.**

| Path | Action | Type |
|---|---|---|
| `deploy/ec2/user-data.sh` [proposed] | New | Infra |
| `deploy/ec2/deploy.sh` [proposed] | New | Infra |
| `deploy/caddy/Caddyfile` [proposed] | New | Infra |
| `deploy/compose/docker-compose.ec2.yml` [proposed] | New | Infra |

**Key tasks.**
- User data: install Docker Engine + Compose plugin (AL2023); verify SSM Agent
  (expected preinstalled — VERIFY); create the deployment directory (e.g.,
  `/opt/taskflow`); fetch the deployment bundle (script + Caddyfile + EC2 compose
  file) from the S3 artifacts bucket. **Bootstrap ordering:** the initial bundle must
  be uploaded to S3 once (documented one-time step or a `workflow_dispatch` run of
  the P9 pipeline) before first boot/first deployment.
- Caddy: `https://app.<domain>` → `frontend:3000`; `https://api.<domain>` →
  `backend:8000`; ACME email from `/taskflow/caddy/acme-email`; persistent
  certificate/account volumes; HTTP→HTTPS redirect; outbound internet available
  (public subnet + IGW).
- EC2 compose: services `caddy`, `backend`, `frontend` + a run-once `migrate`
  definition (recommended invocation: `docker compose run --rm migrate`; alternative:
  direct `docker run` with the backend digest — implementation decision). Only ports
  80/443 published (Caddy); backend 3000/8000 are Compose-internal, never published.
- Deployment script (the controlled sequence — matches §0.4 exactly):
  1. Read the release manifest (S3) → exact backend/frontend digests.
  2. Retrieve the manually bootstrapped SSM SecureString parameters; construct the
     runtime-only `DATABASE_URL=postgresql+psycopg://<user>:<password>@<rds-endpoint>:5432/taskflow?sslmode=require`
     into a protected env file (mode 600; never in Git/images/logs/CFN outputs/GitHub).
  3. Verify RDS reachability (e.g., connection attempt from the backend image).
  4. Run `alembic upgrade head` (one-off). **Stop immediately on failure** — old
     backend keeps serving; release aborts non-zero.
  5. Update backend container; poll internal `GET http://backend:8000/api/tasks`
     until HTTP 200 + valid JSON array (readiness contract, §0.5). Polling mechanism
     (compose exec vs. loopback binding vs. one-off curl container): implementation
     decision.
  6. Update frontend container; verify local/proxy readiness (frontend responds;
     Caddy routes both hosts).
  7. Record deployed digests / release state to S3.
- `CORS_ALLOWED_ORIGINS=https://app.<domain>` on the EC2 runtime (exact origin).

**Verification.**
- Bootstrap the instance (or re-run user data); confirm Docker, SSM, bundle fetch.
- Execute the script once via the SSM console/AWS CLI against a hand-made test
  manifest; observe: migration runs before backend update; readiness enforced; state
  recorded.
- Optional drill: inject a bad `DATABASE_URL` in a sandbox → script must stop before
  backend update.
- After DNS points at the EIP: confirm Caddy obtains ACME certificates and serves
  HTTPS for both hosts.

**Expected result.** Full on-host sequence works against RDS; TLS live; app ports not
publicly exposed.

**Gate.** Sequence executed successfully end-to-end on EC2; failure path stops before
backend update; AC-6.2 prerequisites in place.

---

## Phase 9 — CD Pipeline: Merge-to-Main Deployment + Public Smoke Test

**Objective.** Merge to `main` → automated build → ECR (immutable digests) →
manifest → SSM → migration gate → readiness → frontend → public smoke; fully
automated, no manual deploy steps.

**Dependencies.** P6 (CI gate), P7, P8.

**Files.**

| Path | Action | Type |
|---|---|---|
| `.github/workflows/deploy.yml` (repository root; see P6 naming note) | New | CI |

**Key tasks.**
- **Deploy gate (locked):** `deploy.yml` runs only after the required CI workflow has
  succeeded for the **same commit SHA** on `main`. Use the CI workflow's `workflow_run`
  completion as the deployment trigger, and explicitly require: the triggering CI run
  concluded with `success`, the CI event was a push to `main`, and the deployment
  operates on that exact `workflow_run.head_sha`. Do not deploy pull requests and do
  not silently substitute a different commit SHA. Do not re-run the full CI suite merely
  to establish the deployment gate unless the workflow design requires it.
- Authenticate via GitHub OIDC → scoped AWS role; **short-lived credentials only; no
  static AWS keys in GitHub**.
- Build and push `linux/amd64` images to ECR. Frontend build arg
  `VITE_API_BASE_URL=https://api.<domain>` (value sourced from a GitHub repository
  variable or equivalent non-secret configuration — mechanism: TBD).
- Resolve immutable image digests after push (`aws ecr describe-images` /
  `docker buildx imagetools inspect`).
- Update CloudFormation **only when infrastructure changed**. The exact detection
  mechanism (release-range path inspection vs. change-set strategy) remains TBD and
  must be resolved before finalizing P9. CloudFormation is never the routine
  application-release mechanism.
- Create and upload the release manifest (git SHA, digests, build values, timestamp —
  non-secret) to S3.
- Invoke SSM Run Command (`AWS-RunShellScript`, target by instance tag) → the EC2
  deployment script executes §0.4 steps from "pulls exact image digests" onward; wait
  for command completion; capture output (S3/CloudWatch).
- **Public smoke test** (from GitHub Actions, after SSM success):
  - `GET https://app.<domain>/` → 200, renderable response (spec AC-7.1)
  - `GET https://api.<domain>/api/tasks` → 200 + valid JSON array (backend response +
    database-dependent operation through the public path — spec AC-7.2/7.3)
- Record deployed digests / release state (S3, written by the script).
- On any failure: job fails visibly; rollback path (P10) available.

**Verification.**
```bash
# merge a trivial change to main → observe: CI green → deploy.yml green →
#   images pushed, digests resolved, manifest uploaded, SSM command Succeeded,
#   smoke checks 200/JSON-array, release state recorded
curl -fsS https://app.<domain>/ && curl -fsS https://api.<domain>/api/tasks
```

**Expected result.** Spec AC-6.1–6.6 and AC-7.4 satisfied; automatic redeployment
demonstrated.

**Gate.** One full merge-to-main release completes green, end to end, with no manual
deployment steps.

---

## Phase 10 — Rollback Procedure and Release Documentation

**Objective.** A practical, documented rollback; the release process documented.

**Dependencies.** P9 (a real release exists to roll back from).

**Files.**

| Path | Action | Type |
|---|---|---|
| `docs/release-process.md` | New | Docs |

**Key tasks.**
- Document the release flow `merge → CI gate → build → migrate → deploy → smoke →
  rollback if necessary` (spec AC-9.3) and the CI gating configuration (required
  checks from P6).
- Rollback procedure (practical, single environment): redeploy the previous release
  by re-running the EC2 deployment script against the previous S3 manifest (previous
  ECR digests — immutable, still present; ECR lifecycle policy must retain recent
  images). Database handling: prefer backward-compatible migrations so image rollback
  is feasible; RDS snapshot restore documented as the data-recovery path of last
  resort; **no automatic `alembic downgrade`** as the default mechanism.
- Stop-the-line guidance: failed smoke → leave previous version serving where
  possible, diagnose via SSM output/CloudWatch, then redeploy previous manifest.

**Verification.** Dry-run (or sandbox rehearsal) of the rollback steps against the
previous manifest; confirm documentation is actionable (what to re-point/redeploy,
how DB state is handled).

**Expected result.** Spec AC-8.1/8.2 satisfied.

**Gate.** Documented, actionable rollback; rehearsed or dry-run verified.

---

## Phase 11 — Final Documentation Updates

**Objective.** Remaining required documentation. *(Not created by this plan document;
authored in this phase.)*

**Dependencies.** P9, P10.

**Files.**

| Path | Action | Type |
|---|---|---|
| `docs/testing.md` | New | Docs |
| `docs/deployment.md` | New (do **not** create earlier) | Docs |
| `README.md` | Modify (final) | Docs |

**Key tasks.**
- `docs/testing.md` (spec AC-3.6/9.1): unit-vs-integration split; `TEST_DATABASE_URL`
  contract; migration-based schema setup; CI PostgreSQL service; F2B flow; **the
  authentication applicability note** (N/A for the current unauthenticated TaskFlow
  MVP, clearly separated from official wording — spec §4.3).
- `docs/deployment.md` (spec AC-9.2): deployment topology; selected platform (AWS:
  EC2 + Docker Compose + ECR + RDS PostgreSQL + CloudFormation + GitHub OIDC + SSM +
  Caddy/ACME); public URL; build-time vs runtime configuration; managed PostgreSQL;
  migrations on deploy; secrets/configuration boundaries (SSM Parameter Store
  SecureString; `DATABASE_URL` runtime-only; `VITE_API_BASE_URL` build-time,
  non-secret).
- `README.md` (spec AC-9.4): reproducible local setup (compose), how to run unit and
  integration suites locally.

**Gate.** Spec AC-9.1/9.2/9.4 satisfied.

---

## Phase 12 — Final Verification / Acceptance Gate

**Objective.** Verify the full specification before declaring Module 3 complete.

**Dependencies.** All phases.

**Key tasks.**
- Clean-clone reproducibility: fresh clone → `docker compose up` → working app (AC-4.4).
- Full release drill: merge to `main` → CI gate → build/migrate/deploy → smoke green
  (AC-6.5).
- Walk the spec's AC checklist (§6 of the Product Spec: AC-1.x … AC-9.4) item by item
  and record results.
- Secrets scan: no secrets/`.env`/credentials/generated DB files committed; no secrets
  in image layers or CloudFormation outputs.
- Repository hygiene: artifacts under `module-3/` (except `.github/workflows/`);
  deliverables checklist (Product Spec §8) fully ticked.
- Confirm OD-4 closed and every plan-level TBD resolved or consciously accepted.

**Gate (Module 3 acceptance).** All Product Spec ACs verified; deliverables complete;
public URL live with automatic redeployment and documented rollback.

---

## Appendix A — TBD / NEEDS VERIFICATION Register

| # | Item | Status | Where resolved / verified |
|---|---|---|---|
| T1 | Workflow filenames at repo root (`ci.yml`/`deploy.yml` per spec §8) vs any module-scoped naming convention | Open naming confirmation | P6 kickoff |
| T2 | Frontend script names, Node/bun versions, engine constraints (`package.json` not in evidence) | NEEDS VERIFICATION | P4 |
| T3 | Backend Python version, existing lint configuration (`pyproject.toml` details not in evidence) | NEEDS VERIFICATION | P1/P6 |
| T4 | `db.t4g.micro` + PostgreSQL 16 orderability, `t3.small` availability/pricing in `ap-southeast-1` (account-dependent preflight) | NEEDS VERIFICATION | P7 |
| T5 | Current AL2023 x86_64 AMI resolution via SSM public parameter (verify exact current path) | NEEDS VERIFICATION | P7 |
| T6 | SecureString bootstrap mechanism | **LOCKED:** manual `aws ssm put-parameter` | P7 |
| T7 | TaskFlow DB user model/bootstrap | **LOCKED:** one dedicated `taskflow` user for backend + Alembic; created once using privileged RDS master/admin bootstrap; master never used at runtime | P7/P8 |
| T8 | Internal readiness polling mechanism on EC2 (compose exec vs. loopback binding vs. one-off container) | Open implementation detail | P8 |
| T9 | F2B test tooling (Playwright vs. Node client test) | Open implementation detail | P3 |
| T10 | `VITE_API_BASE_URL` production value sourcing in GitHub (variable mechanism) | Open implementation detail | P9 |
| T11 | Deploy gating mechanism | **LOCKED:** successful CI for same commit SHA on `main` gates `deploy.yml`; prefer `workflow_run` | P9 |
| T12 | CloudFormation conditional-update trigger (path inspection vs. change-set) | Open implementation detail | P9 |
| T13 | SSM Agent preinstalled on AL2023 (verify at bootstrap) | NEEDS VERIFICATION | P8 |
| T14 | Nitro runtime port configuration in container (PORT env behavior) | NEEDS VERIFICATION | P4 |
| T15 | `.gitignore` current coverage | NEEDS VERIFICATION | P0 |
| T16 | First-bundle upload to S3 (one-time bootstrap step) mechanism | Open implementation detail | P8 |
| T17 | RDS master/admin credential acquisition and temporary-storage mechanism for the one-time `taskflow` user bootstrap | **Pre-P7/P8 security decision:** must be explicitly documented and approved; never a runtime application credential | P7/P8 |

### Appendix A.1 — Decision handling

- Items marked **LOCKED** are finalized project decisions and must not be re-decided by
  coding agents.
- Items marked **Open implementation detail** may be selected during the named phase
  if the choice stays within the locked architecture and Product Spec.
- Items marked **NEEDS VERIFICATION** require evidence or account-level checks; do not
  invent a value merely to unblock implementation.
- Deployment-time user inputs U1–U6 are not architecture decisions; resolve them only
  when the affected phase requires them.
- Separate runtime/migration DB users are explicitly future hardening for Module 4+ and
  are not to be implemented in Module 3.
- T17 is a pre-execution security gate: the exact master/admin credential acquisition and
  temporary-storage mechanism must be documented before the one-time DB-user bootstrap;
  it must never become the runtime application credential.

## Appendix B — Time-Sensitive AWS Facts Policy

Live web verification was not performed during the authoring of this plan. All
time-sensitive AWS facts (instance/DB class orderability, AMI identifiers, engine
versions, pricing/Free Tier, SSM public parameter paths) are carried as **explicit
preflight steps in P7/P8** — which the architecture decision record itself requires,
because these values are account- and time-dependent. No AWS fact in this plan should
be treated as verified until its preflight has run against the target account in
`ap-southeast-1`.
