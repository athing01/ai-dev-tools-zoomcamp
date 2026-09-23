# Product Specification — TaskFlow

## Module 3: PostgreSQL, Migrations, Integration Tests, Containers, CI/CD, Deployment

**Version:** 1.3
**Status:** Scope-audited revision of v1.2
**Supersedes:** Product Specification v1.2

> **Provenance note (read first):** The full text of v1.2 was not available in this revision session. This v1.3 was produced by applying the locked scope-audit decisions to the v1.2 artifacts that were referenced in the audit (R6.1, ENV-1 through ENV-4, the deliverables checklist, the Rubric Coverage Matrix, the Open Decisions Register, and the requirement-to-AC mappings) together with the locked architecture decisions and verified POC evidence. Requirement IDs not referenced by the audit have been reconstructed on a consistent scheme. If the actual v1.2 contains additional IDs, sections, or ACs not addressed here, apply the same removal/retention rules to them; do not treat reconstruction gaps as deletions.

---

## 1. Document Control

| Field | Value |
|---|---|
| Product | TaskFlow (mini Kanban task manager) |
| Carried forward from | Module 2 baseline |
| Module 3 goals | PostgreSQL, Alembic migrations, integration tests, Docker/Compose, CI/CD, public deployment |
| Source of truth | Official Module 3 requirements/rubric (see §2) |

**Change history**

| Version | Change |
|---|---|
| 1.2 | Prior baseline (included staging/production environment architecture; auth-adjacent test scope; heavyweight rollback requirements) |
| 1.3 | Scope audit applied: removed staging/production environment architecture; recorded authentication as N/A; simplified rollback to a practical documented procedure; retained public deployment, CI/CD, smoke test, and rollback as confirmed scope; architecture decisions re-categorized as locked decisions / constraints / baseline / POC evidence rather than course requirements |

---

## 2. Source Hierarchy and Authority

Requirements in this specification are derived from the following sources, in descending authority:

1. **Official Module 3 requirements/rubric**
2. **Locked architecture decisions and verified POC evidence**
3. **Module 2 baseline**
4. **Companion article implementation details**
5. **Prior Product Specification versions**

The Product Specification is **not** the source of truth for course requirements. A requirement is not mandatory merely because a prior version of this document contained it. Where this specification interprets an official source item in the context of TaskFlow's actual capability set, the interpretation is explicitly labeled as such (see §12).

**Known source inconsistencies** are recorded in §12 and must not be silently resolved in either direction.

---

## 3. System Overview (Module 2 Baseline)

### 3.1 Backend

- FastAPI application factory: `create_app(repo=None)`
- Repository abstraction: `TaskRepository`
- In-memory repository implementation (used by unit tests)
- SQLAlchemy repository implementation (backs the application)
- Runtime database at end of Module 2: SQLite

### 3.2 Frontend

- React 19, TanStack Start, Vite, TanStack Query
- Browser-side API client using `VITE_API_BASE_URL`
- API calls of the form `${API_BASE_URL}/api/tasks`
- Custom server entry: `src/server.ts`
- Build toolchain: `@lovable.dev/vite-tanstack-config` (manages the Nitro plugin); Nitro 3 beta; Vite 8

### 3.3 Domain/API boundaries (preserved)

The existing TaskFlow domain model, API surface, and repository boundaries are a **baseline** and must be preserved. Module 3 changes infrastructure and delivery, not the product's functional behavior.

---

## 4. Module 3 Scope

### 4.1 In scope (confirmed)

- PostgreSQL as the runtime database (replacing SQLite)
- Alembic migrations, including migrations at deploy time
- Integration tests against a real PostgreSQL instance
- Frontend-to-backend integration flow
- Docker images and Docker Compose topology
- GitHub Actions CI with gating on pull requests
- GitHub Actions CD with automatic deployment on merge to `main`
- Deployment to a single public application URL
- Managed PostgreSQL for the deployed application
- Post-deployment smoke test
- Documented rollback path
- README reproducibility for local setup
- Documentation: `docs/testing.md`, `docs/deployment.md`, `docs/release-process.md`

### 4.2 Out of scope (this module)

- **Authentication** — N/A for the current TaskFlow application scope. See §4.3.
- Staging/production environment separation — removed by scope audit; see §12.1. (Environment separation is subsequent DevOps work in the companion article Part 4, not Module 3.)
- Any functional/feature changes to TaskFlow beyond infrastructure and delivery

### 4.3 Authentication applicability note

TaskFlow currently has **no** user identity model, user/session/token model, task ownership model, or authorization model. The official Module 3 text mentions integration tests covering auth. The available Module 2 and Module 3 homework/submission evidence does not establish that students must add authentication to an existing project that does not have it.

**Project-specific interpretation (not official wording):** because TaskFlow has no authentication capability, auth-related integration/E2E testing is **N/A for the current TaskFlow application scope**. This interpretation is based on TaskFlow's actual capability set and must not be presented as a quotation or paraphrase of the official Module 3 source. `docs/testing.md` must document this applicability determination (see R9.1).

If a later, authoritative rubric artifact proves authentication mandatory, this section must be revised through the normal change process — not implemented ad hoc.

### 4.4 Non-goals

- AWS is **not** a mandatory provider. AWS appears in the companion article as the implementation example and may be selected as the deployment platform, but no requirement in this specification mandates it.
- Kubernetes is **not** required.
- No provider-specific architecture unless required by the selected deployment platform.
- No same-origin `/api` proxy (see §5).
- No SSR/server-function data-fetching redesign (see §5).
- No authentication, authorization, roles, JWT, or sessions (see §4.3).

---

## 5. Architecture Decisions

These are **locked architecture decisions, constraints, baseline facts, and verified POC evidence** — not independent Module 3 course requirements. They are retained because they are needed to implement TaskFlow correctly and are consistent with the confirmed Module 3 scope.

| ID | Decision / fact | Category |
|---|---|---|
| A-1 | Browser talks directly to the backend public origin (`${API_BASE_URL}/api/...`); no same-origin `/api` proxy layer in the frontend | Locked architecture decision |
| A-2 | `VITE_API_BASE_URL` remains build-time, browser-visible configuration; no runtime injection mechanism required for Module 3 | Locked architecture decision |
| A-3 | No SSR/server-function data-fetching redesign; existing TanStack Query browser-side client is preserved | Locked architecture decision |
| A-4 | Frontend runtime is Nitro `node-server`, packaged as a multi-stage Docker image, run via `node .output/server/index.mjs`; the `cloudflare-module` default preset of the build wrapper is explicitly overridden | Locked architecture decision |
| A-5 | Backend uses CORS with an exact-origin allowlist (`CORS_ALLOWED_ORIGINS`); no wildcard origins | Locked architecture decision |
| A-6 | Runtime database is PostgreSQL; SQLite is not the Module 3 runtime database | Locked architecture decision |
| A-7 | Alembic manages schema migrations; migration runs as a separate Compose step (`postgres` → `migrate` → `backend` → `frontend`) and as a deploy-time step in CD | Locked architecture decision |
| A-8 | PostgreSQL enum for task status uses the explicit enum name `task_status` | Locked architecture decision |
| A-9 | Custom frontend server entry `src/server.ts` must run under the Nitro `node-server` preset; Node-version compatibility in the Docker base image is a build constraint | Constraint |
| A-10 | Module 2 domain/API/repository boundaries are preserved | Baseline |
| A-11 | Verified: Nitro build outside the Lovable sandbox does not set `LOVABLE_SANDBOX`/`DEV_SERVER__PROJECT_PATH`, so the wrapper's forced Cloudflare preset does not apply; user Nitro options can override the default preset. The override must be verified as actually honored in a real build before implementation is considered complete (POC evidence; residual verification noted in the Open Decisions Register) | Verified POC evidence |
| A-12 | Repository abstraction (`TaskRepository`, in-memory and SQLAlchemy implementations) is preserved; integration tests target the SQLAlchemy repository against real PostgreSQL | Baseline |

---

## 6. Product Requirements

Acceptance criteria use the existing checklist style. Each requirement is traceable to its Module 3 source basis (§10) and to its ACs.

### R1 — Runtime Database: PostgreSQL

The application runs against PostgreSQL in all non-test runtime contexts.

**ACs**

- **AC-1.1** — The deployed application and the Docker Compose–based local environment both use PostgreSQL; neither uses SQLite at runtime.
- **AC-1.2** — The SQLAlchemy repository operates against PostgreSQL without repository-interface changes.
- **AC-1.3** — The PostgreSQL enum for task status uses the explicit name `task_status` (per A-8).

### R2 — Database Migrations: Alembic

**ACs**

- **AC-2.1** — An Alembic migration chain exists that can create the current schema from an empty PostgreSQL database.
- **AC-2.2** — Migrations run as a distinct step in the Compose topology before the backend starts.
- **AC-2.3** — Migrations run as part of deployment (see R6.4).
- **AC-2.4** — Integration tests set up schema via the Alembic migration chain (see R3).

### R3 — Testing

**ACs**

- **AC-3.1** — Unit tests exercise the application via the in-memory repository, with no database dependency.
- **AC-3.2** — Integration tests run against a real PostgreSQL instance (not SQLite, not mocks).
- **AC-3.3** — Integration-test schema setup uses the Alembic migration chain (or a documented equivalent consistent with AC-2.1).
- **AC-3.4** — CI provides a PostgreSQL service for integration tests.
- **AC-3.5** — The frontend-to-backend integration flow is tested (frontend API client ↔ backend API, including the CORS configuration path).
- **AC-3.6** — `docs/testing.md` documents the unit-vs-integration split, real-PostgreSQL integration tests, migration setup, CI PostgreSQL service, frontend-to-backend flow, and the authentication applicability note (§4.3). *(Auth applicability is documentation of a scope determination, not an auth test requirement.)*

### R4 — Containerization

**ACs**

- **AC-4.1** — A `Dockerfile` (or Dockerfiles) builds reproducible images for backend and frontend.
- **AC-4.2** — The frontend image runs the Nitro `node-server` output (per A-4).
- **AC-4.3** — `docker-compose.yml` defines the topology `postgres` → `migrate` → `backend` → `frontend` with correct service ordering/dependencies.
- **AC-4.4** — `docker compose up` from a clean clone produces a working local application, consistent with the README reproducibility requirement (R9.4).

### R5 — Continuous Integration

**ACs**

- **AC-5.1** — `.github/workflows/ci.yml` runs linting, unit tests, integration tests, and a container build on every pull request.
- **AC-5.2** — Pull requests are gated: merge to `main` requires CI success.

### R6 — Deployment and Release (CD)

> **Removed:** R6.1 ("Staging and production") — removed by scope audit (§12.1). Remaining R6.x IDs are **not renumbered**.

- **R6.2 — Public deployment.** The application is deployed to a single public application URL on a suitable platform. No specific provider is mandated; AWS is the companion-article example and may be chosen.
- **R6.3 — Managed PostgreSQL.** The deployed application uses a managed PostgreSQL service.
- **R6.4 — Deploy-time migrations.** Database migrations run as part of the automated deployment flow.
- **R6.5 — Automatic redeployment.** Merge to `main` triggers the CI/CD gate, build, migrate, and deploy; the application is automatically redeployed without manual steps beyond the merge.

**Intended release flow (normative for this specification):**

```
PR
→ lint / unit / integration / container build
→ merge to main
→ CI/CD gate
→ build
→ migrate
→ deploy
→ post-deployment smoke test
```

**ACs**

- **AC-6.1** — A public application URL serves the TaskFlow frontend.
- **AC-6.2** — The deployed backend is reachable from the browser via the configured API base URL, with CORS configured per A-5.
- **AC-6.3** — The deployed application uses managed PostgreSQL (R6.3).
- **AC-6.4** — Migrations execute during the automated deployment flow before the new application version serves traffic (ordering may be satisfied by any practical mechanism; the requirement is that deploys migrate).
- **AC-6.5** — Merging to `main` results in a completed automated deployment (R6.5).
- **AC-6.6** — `.github/workflows/deploy.yml` implements the release flow above.

### R7 — Post-Deployment Smoke Test

The Module 3 source explicitly requires a post-deploy smoke test.

**ACs (acceptance constraints; exact smoke implementation is an implementation decision — see Open Decisions Register)**

- **AC-7.1** — The smoke test verifies that the frontend public route responds successfully.
- **AC-7.2** — The smoke test verifies that the backend responds.
- **AC-7.3** — The smoke test verifies that the backend can perform a database-dependent operation.
- **AC-7.4** — The smoke test runs against the single public deployment target after each automated deployment.

> A specific health endpoint is **not** a course requirement and must not be presented as one; the source does not require a particular endpoint. Any health-endpoint choice is an implementation decision.

### R8 — Rollback

The Module 3 source explicitly requires a **documented rollback path**.

- **R8.1 — Documented rollback procedure.** A practical, documented rollback procedure exists for the deployment, sufficient for a maintainer to follow in the event of a failed or bad deployment.

**ACs**

- **AC-8.1** — `docs/release-process.md` documents the rollback procedure as the final step of the release flow (`merge → CI gate → build → migrate → deploy → smoke → rollback if necessary`).
- **AC-8.2** — The documented procedure is concrete enough to be actionable for the selected platform (what to re-point/redeploy, and how database state is handled), while the exact mechanism remains an implementation decision.

> **Implementation guidance (not requirements):** expand/contract migration strategy, an Alembic downgrade policy, per-service image rollback mechanics, and provider-specific rollback commands are sound engineering practices and may be adopted, but they are **not** Module 3 rubric requirements and must not be stated as such.

### R9 — Documentation and Reproducibility

**ACs**

- **AC-9.1** — `docs/testing.md` satisfies AC-3.6.
- **AC-9.2** — `docs/deployment.md` documents: deployment topology, selected deployment platform, public application URL, runtime/build-time configuration, managed PostgreSQL, migrations on deploy, and secrets/configuration boundaries. *(No staging/production configuration content.)*
- **AC-9.3** — `docs/release-process.md` documents `merge → CI gate → build → migrate → deploy → smoke → rollback if necessary`. *(No staging → production promotion.)*
- **AC-9.4** — The README enables reproducible local setup from a clean clone (compose-based; consistent with AC-4.4).

---

## 7. Environment and Configuration Model

> **Removed:** ENV-1 through ENV-4 (staging environment, production environment as a separate Module 3 deployment target, per-environment frontend builds/public URLs, and environment parity) — removed by scope audit (§12.1). No replacement ENV requirements are introduced. The configuration model below is descriptive, tied to the locked architecture decisions in §5.

**Deployment configuration model.** Module 3 defines the required public deployment target. The specification does not prescribe separate staging/production environments.

| Variable | Scope | Nature |
|---|---|---|
| `DATABASE_URL` | Backend | Runtime |
| `CORS_ALLOWED_ORIGINS` | Backend | Runtime; exact-origin allowlist (A-5) |
| `VITE_API_BASE_URL` | Frontend | Build-time, browser-visible (A-2) |

Secrets and configuration boundaries (which values are build-time vs. runtime, and where secrets live) must be documented in `docs/deployment.md` (AC-9.2).

---

## 8. Deliverables Checklist

- [ ] `tests/integration/`
- [ ] `Dockerfile`
- [ ] `docker-compose.yml`
- [ ] `.github/workflows/ci.yml`
- [ ] `.github/workflows/deploy.yml`
- [ ] `docs/testing.md`
- [ ] `docs/deployment.md`
- [ ] `docs/release-process.md`
- [ ] Public application URL (R6.2)
- [ ] Automatic redeploy after merge to `main` (R6.5)
- [ ] Reproducible local setup from README (R9.4)

> **Removed from checklist:** staging deployment files, production deployment files, staging configuration, production configuration, staging/production URLs.

---

## 9. — *(reserved; numbering preserved from v1.2 structure)*

---

## 10. Rubric Coverage Matrix

| Module 3 source item | Covered by | Notes |
|---|---|---|
| Integration tests | R3, AC-3.1–3.4, AC-3.6 | |
| Integration tests "covering auth" | §4.3, AC-3.6 | Applicability documented as N/A for current TaskFlow scope; project-specific interpretation, not official wording |
| Containerization | R4 | |
| SQLite → PostgreSQL | R1, A-6 | |
| Deployment (public) | R6.2, AC-6.1 | Single public deployment target |
| "Add staging vs. production environments, a post-deploy smoke test, and a documented rollback path" | Smoke: R7; Rollback: R8; Staging/production: §12.1 | Source inconsistency: this "You will" bullet is not supported by the Module summary, deliverables, Homework 3, or the companion article; v1.3 does not expand it into an environment architecture |
| AWS deployment | R6.2 (provider-agnostic) | Companion-article example only; not mandatory (§4.4) |
| GitHub Actions automation / CI/CD | R5, R6, AC-5.x, AC-6.x | |
| Managed PostgreSQL | R6.3, AC-6.3 | |
| Migration on deploy | R6.4, AC-2.3, AC-6.4 | |
| Post-deploy smoke test | R7 | Implementation decision for mechanism |
| Documented rollback path | R8, AC-8.1–8.2 | Simplified to practical documented procedure |
| Deliverable files | §8 | Unchanged set |
| README reproducibility | R9.4, AC-9.4 | |

---

## 11. Open Decisions Register

| ID | Decision | Status | Constraint |
|---|---|---|---|
| OD-1 | Deployment platform/provider selection | Open | Must support the public deployment outcome (R6.2, R6.3); no provider mandated (§4.4) |
| OD-2 | Exact smoke-test mechanism | Open | Must satisfy AC-7.1–7.4; no specific endpoint required by the course |
| OD-3 | Exact rollback mechanism | Open | Must satisfy AC-8.1–8.2; expand/contract, downgrade policy, image rollback are guidance, not requirements |
| OD-4 | Verification that the Nitro `node-server` preset override is honored by the build wrapper in a real build (residual POC verification per A-11) | Open — verification task, not a design decision | Must be confirmed before frontend containerization is considered done |
| OD-5 | Secrets/configuration management approach for the deployed environment | Open | Must be documented per AC-9.2 |

> **Removed from register:** staging/production promotion sequencing, staging/production domains and URLs, per-environment build strategy, staging-specific smoke tests.

---

## 12. Source Inconsistencies and Interpretations (must not be silently resolved)

### 12.1 Staging/production environments

The Module 3 page **does** mention staging in its "You will" list: *"Add staging vs. production environments, a post-deploy smoke test, and a documented rollback path."*

However, the source set is **internally inconsistent**:

- The Module 3 **Module summary** describes the flow as: local application → public deployment → integration/E2E tests → containerization → SQLite to Postgres → AWS deployment → GitHub Actions automation — with no staging/production separation.
- The Module 3 **deliverables** do not specify separate staging and production environments.
- **Homework 3** does not specify staging/production.
- The **companion article Part 3** does not implement staging/production; environment separation is discussed as subsequent DevOps work in Part 4.

**Conclusion (v1.3, locked):** the single inconsistent "You will" bullet, on its own, does not justify expanding into the full staging/production environment architecture present in v1.2. That architecture has been removed. This is a scope decision based on the weight of the source set — **not** a claim that the Module 3 page never mentions staging.

### 12.2 Authentication in integration tests

See §4.3. The interpretation is project-specific (based on TaskFlow's capability set) and is explicitly distinguished from the official Module 3 wording, which mentions integration tests covering auth without (in the available evidence) requiring students to add authentication to a project that lacks it. **Not claimed:** that the official text says "where applicable" — it does not use that wording.

### 12.3 Remaining ambiguities (recorded, unresolved)

- Whether the official Module 3 rubric, once fully available, treats the "staging vs. production" bullet as graded or aspirational.
- Whether any authoritative rubric artifact makes authentication mandatory for projects that lack it.

If either ambiguity is resolved by authoritative evidence, revise §4.2/§4.3 and §12 through the change process.

---

## Revision Summary (v1.2 → v1.3)

**Removed — staging/production scope**

- R6.1 ("Staging and production") — removed; remaining R6.x IDs intentionally **not renumbered**.
- ENV-1, ENV-2, ENV-3, ENV-4 — removed in full (they existed solely to model staging/production: environment definitions, per-environment public URLs, per-environment frontend builds, environment parity).
- Staging → production promotion, sequencing, domains/URLs, staging-specific smoke tests, deployment automation across two environments, and all related ACs, deliverable-checklist entries, and Open Decisions Register entries.
- The Part 4 development → production promotion workflow was **not** imported.
- Basis: source inconsistency (§12.1) — not a claim that the Module 3 page omits staging.

**Removed/recorded — authentication implementation scope**

- No login, registration, JWT, session/cookie auth, roles/authorization, or auth-specific integration/E2E tests.
- Authentication is represented as: "N/A for the current TaskFlow application scope," documented in `docs/testing.md` (AC-3.6) with the project-specific interpretation clearly separated from official wording (§4.3, §12.2).

**Simplified — rollback**

- R8 now requires a practical, documented rollback procedure (R8.1, AC-8.1–8.2). Expand/contract migrations, Alembic downgrade policy, per-service image rollback mechanics, and provider-specific rollback commands are reclassified as implementation guidance, not requirements.

**Retained — public deployment + CI/CD**

- Single public application URL, provider-agnostic deployment, managed PostgreSQL, deploy-time migrations, automatic redeploy on merge to `main`, full CI gating flow, post-deploy smoke test (rewritten for the single deployment target — removed "after every deploy in every environment" phrasing), README reproducibility. AWS remains a non-mandated example (§4.4).

**Requirement IDs removed or rewritten**

- **Removed:** R6.1, ENV-1, ENV-2, ENV-3, ENV-4.
- **Rewritten:** R6 (deployment section restructured around R6.2–R6.5), R7 (single-target wording), R8 (simplified), §7 Environment and Configuration model (descriptive, ENV IDs not reintroduced), §8 deliverables checklist, §10 Rubric Coverage Matrix, §11 Open Decisions Register.
- **Preserved:** R1–R5, R9, A-1 through A-12 (re-categorized as locked decisions/constraints/baseline/POC evidence rather than course requirements), all Module 3 deliverable files.

**Remaining source ambiguities — not silently resolved**

- §12.3: (a) whether the "staging vs. production" bullet is graded; (b) whether any authoritative artifact mandates authentication. Both remain open pending authoritative rubric evidence.

**Known limitation of this revision**

- v1.2's full text was not available; this document is a faithful application of the locked audit decisions to the referenced v1.2 artifacts. Any v1.2 requirement IDs, ACs, or sections not referenced by the audit should be carried forward unchanged under the same removal/retention rules.