# Model-Assisted Review — Semgrep Baseline

## Review Identity

| Field | Value |
|---|---|
| Repository | `ai-dev-tools-zoomcamp` |
| Audit baseline | `fba6a3945b0b59069580a2e2df6423f2503eb7eb` |
| Scanner | Semgrep |
| Scanner version | `1.179.0` |
| Raw result count | 39 |
| Scanner parser/error records | 9 |
| Review status | Model-assisted review; human validation/disposition pending |

## Review Rule

Semgrep output is scanner evidence, not an automatically confirmed security finding.

- `candidate`: merits security finding review and possible remediation.
- `likely_false_positive`: source semantics strongly indicate the rule does not describe the actual threat.
- `inherited_or_out_of_scope`: observation exists in a protected baseline or outside P6-A remediation scope.
- `needs_more_evidence`: source/configuration evidence is insufficient for reliable disposition.

Human validation and disposition are required before an observation becomes a confirmed finding.

## Triage Summary

| Group | Observations | Model-assisted assessment | Human validation |
|---|---:|---|---|
| M4 mutable GitHub Action references | 19 | `candidate` | Required |
| M3 mutable GitHub Action references | 15 | `inherited_or_out_of_scope` | Required |
| `workflow_run` target-code checkout | 2 | `likely_false_positive` | Required |
| Bun minimum release age | 1 | `candidate` | Required |
| uv dependency cooldown | 1 | `candidate` | Required |
| Dynamic `urllib` URL in responder | 1 | `needs_more_evidence` | Required |

## 1. M4 Mutable Action References

Semgrep reports 19 mutable-action observations across `ci-module-4.yml`, `deploy-module-4.yml`, and `promote-module-4.yml`. The reviewed source also contains examples of full-SHA-pinned actions.

Assessment: **candidate**.

The observations share a common supply-chain hardening root cause. Do not create 19 duplicate findings; normalize to one repository/workflow-level finding with all affected locations as evidence.

Human decision: remediate by pinning M4 actions to verified full commit SHAs, or accept the residual risk with explicit rationale, owner, and review date.

## 2. M3 Mutable Action References

Semgrep reports 15 mutable-action observations across the protected M3 workflows `ci.yml` and `deploy.yml`.

Repository review evidence records no diff to these workflows between `cfc5189ffe74e63510b5f041bf38e9b933c5ea9a` and the P5 merge baseline `fba6a3945b0b59069580a2e2df6423f2503eb7eb`.

Assessment: **inherited_or_out_of_scope**.

This does not claim the hardening opportunity is harmless; it records that P6-A must preserve the established M3 protected workflow boundary unless an authoritative requirement explicitly changes that boundary.

Human decision: record an explicit inherited/protected-baseline disposition and, if desired, track remediation separately.

## 3. `workflow_run` Target-Code Checkout

Semgrep reports the target-code-checkout rule for `deploy-module-4.yml` and `deploy.yml`.

Source review shows the deployment gate requires:

```text
workflow_run.conclusion == success
workflow_run.event == push
workflow_run.head_branch == main
```

The M4 workflow sets `RELEASE_SHA` to `github.event.workflow_run.head_sha`, checks out that exact SHA, and verifies `git rev-parse HEAD` matches it. The checked-out M4 files are packaged as a fixed deployment bundle rather than used as an arbitrary PR build/test payload.

Assessment: **likely_false_positive for the specific PR-code pwn-request scenario**.

GitHub's current guidance confirms that `workflow_run` is privileged and warns against checking out and executing untrusted pull-request code. The reviewed M4/M3 gates explicitly reject upstream `pull_request` runs and bind the checkout to the successful `push` run's immutable `head_sha`.

Human decision: validate the current GitHub workflow semantics and record whether the Semgrep observation is a false positive under the current gate. No workflow change should be made solely to reduce this scanner result.

## 4. Bun Minimum Release Age

Observation: `module-4/frontend/bunfig.toml:4`.

Assessment: **candidate**.

This is a dependency-resolution hardening issue distinct from GitHub Action pinning. Validate compatibility with the existing Bun lockfile/build before changing configuration.

## 5. uv Dependency Cooldown

Observation: `module-4/incident-response/pyproject.toml:10`.

Assessment: **candidate**.

This is a dependency-resolution hardening issue for the responder environment. Validate compatibility with the locked dependency set before remediation.

## 6. Dynamic `urllib` URL in Responder

Observation: `module-4/incident-response/responder.py:379`.

Reviewed source shows:

```text
RESPONDER_BASE_URL -> endpoint -> urllib.request.urlopen(...)
RESPONDER_API_KEY  -> authorization header containing the configured responder credential
```

The URL is runtime configuration, not derived from incident evidence or model output. The repository snapshot does not contain the external control-plane assignment for `RESPONDER_BASE_URL`, so the trusted configuration boundary is not fully evidenced by source alone.

Assessment: **needs_more_evidence**.

Do not dismiss this merely because the value is an environment variable. Validate who can set it, where it is sourced, and whether the responder can run with credentials/file access that make a malicious scheme or host consequential.

Possible defense-in-depth options for later consideration include requiring HTTPS and allowlisting the responder endpoint. These are remediation options, not conclusions of the current review.

## 7. Scanner Coverage Limitations

Semgrep completed the scan but emitted 9 parser/partial-parsing records affecting:

- `module-4/incident-response/runbooks/verify-recovery.sh`
- `module-4/deploy/ec2/deploy.sh`
- `module-4/deploy/ec2/user-data.sh`
- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/promote-module-4.yml`

These are scanner coverage limitations, not security findings. The affected files require complementary source review and, where useful, language-specific linting.

## Human Validation Record

| Review item | Reviewer | Disposition | Date | Notes |
|---|---|---|---|---|
| M4 mutable action references | _pending_ | _pending_ | _pending_ | |
| M3 mutable action references | _pending_ | _pending_ | _pending_ | |
| M4 `workflow_run` checkout | _pending_ | _pending_ | _pending_ | |
| M3 `workflow_run` checkout | _pending_ | _pending_ | _pending_ | |
| Bun minimum release age | _pending_ | _pending_ | _pending_ | |
| uv dependency cooldown | _pending_ | _pending_ | _pending_ | |
| responder dynamic URL | _pending_ | _pending_ | _pending_ | |

## References

- GitHub Actions Secure use reference: https://docs.github.com/en/actions/reference/security/secure-use
- GitHub workflow events: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
