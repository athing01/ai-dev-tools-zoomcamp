# Human Validation / Disposition Worksheet — Semgrep Baseline

## Review basis

- Repository: `ai-dev-tools-zoomcamp`
- Audit baseline: `fba6a3945b0b59069580a2e2df6423f2503eb7eb`
- Scanner: Semgrep `1.179.0`
- Raw observations: 39
- Parser/error records: 9
- Model-assisted review: completed
- Human validation/disposition: completed
- Review date: `2026-10-07`
- Remediation checkpoint: `7906eb5fbe3c75bb967926e048b28d4cbf912931`
- Final Semgrep verification scan: `module-4/security-audit/runs/semgrep/p6-remediation-final/semgrep.json`

## Grouped observations

| ID | Observation group | Count | Proposed status | Human disposition | Remediation status |
|---|---|---:|---|---|---|
| SEC-SG-M4-ACTION-PINNING | Mutable GitHub Actions references in M4 workflows | 19 | candidate | **remediate** | **Verified / closed** — all affected M4 third-party actions are pinned to verified full commit SHAs |
| SEC-SG-M3-ACTION-PINNING | Mutable GitHub Actions references in protected M3 workflows | 15 | inherited / out of P6-A remediation scope | **inherited / out-of-scope** | None in P6-A |
| SEC-SG-WORKFLOW-RUN-CHECKOUT | `workflow_run` target-code checkout | 2 | likely false positive | **false_positive** | No workflow change required |
| SEC-SG-BUN-RELEASE-AGE | Bun minimum release age below Semgrep recommendation | 1 | hardening gap / candidate | **accept hardening gap** | No remediation required for P6-A; retain as accepted hardening gap |
| SEC-SG-UV-COOLDOWN | uv dependency cooldown absent | 1 | candidate | **remediate** | **Verified / closed** — uv `exclude-newer` policy validated with locked dependency resolution |
| SEC-SG-RESPONDER-URL | Dynamic responder `urllib` URL | 1 | needs more evidence | **false_positive** | No remediation required for reviewed configuration; re-review if endpoint provenance/control changes |

## Human disposition record

### SEC-SG-M4-ACTION-PINNING

**Disposition:** `remediate`

Semgrep reports mutable Action references in:

- `.github/workflows/ci-module-4.yml`
- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/promote-module-4.yml`

These are actual mutable references. The observations share a common root cause and should be handled as one grouped remediation rather than 19 duplicate findings.

**Rationale:** M4 workflow dependencies are within the P6-A remediation boundary. Third-party GitHub Actions should be pinned to verified full commit SHAs to remove mutable tag/branch resolution from the reviewed M4 workflow path.

**Remediation status:** Verified / closed. Final verification confirms every affected third-party Action reference is pinned to a verified 40-character commit SHA, and the final Semgrep scan reports zero M4 mutable-action observations.

### SEC-SG-M3-ACTION-PINNING

**Disposition:** `inherited / out-of-scope`

Affected protected M3 workflows:

- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`

These workflows are protected M3 baseline assets. The P5 merge preserved them unchanged relative to the M3 parent baseline.

**Rationale:** The observation is inherited from the protected M3 baseline and is outside the P6-A remediation scope. P6-A must preserve the M3 security/workflow material trail rather than silently rewrite the baseline during Module 4 finalization.

**Remediation status:** None in P6-A. Any future remediation belongs to the M3 baseline maintenance scope.

### SEC-SG-WORKFLOW-RUN-CHECKOUT

**Disposition:** `false_positive`

Affected files:

- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/deploy.yml`

**Rationale:** Semgrep detects the generic `workflow_run` plus checkout pattern associated with privileged workflows consuming upstream workflow context. In the reviewed implementation, the privileged workflow explicitly gates on successful upstream completion, `push` event, and `main` branch; checks out `github.event.workflow_run.head_sha`; and verifies that the checked-out revision matches that immutable SHA. This closes the specific PR-code checkout threat represented by the rule in the reviewed path. `workflow_run` itself remains a security-sensitive release boundary and should not be considered generically safe.

**Remediation status:** No workflow change required for this observation.

### SEC-SG-BUN-RELEASE-AGE

**Disposition:** `accept hardening gap`

Affected file:

- `module-4/frontend/bunfig.toml`

The repository already sets:

```toml
minimumReleaseAge = 86400
```

Semgrep recommends 604800 seconds (7 days), so the source does not lack a release-age control; it uses a shorter 24-hour policy.

**Rationale:** This is a supply-chain hardening gap rather than an absent control. The existing 24-hour minimum release age provides a deliberate delay, while the scanner recommends a stronger 7-day policy. For P6-A, retain the current policy and record the gap rather than changing build behavior without a compatibility decision.

**Remediation status:** Accepted / no P6-A remediation. Revisit if supply-chain hardening requirements or build compatibility decisions change.

### SEC-SG-UV-COOLDOWN

**Disposition:** `remediate`

Affected file:

- `module-4/incident-response/pyproject.toml`

No `exclude-newer` dependency cooldown is configured.

**Rationale:** This is an actionable supply-chain hardening control within the P6-A scope. Add the uv dependency cooldown policy and validate that lockfile/reproducibility behavior remains correct.

**Remediation status:** Verified / closed. The uv policy is present, `uv lock --check` and `uv sync --locked` succeeded, and the final Semgrep scan reports zero uv cooldown observations.

### SEC-SG-RESPONDER-URL

**Disposition:** `false_positive`

Affected source:

- `module-4/incident-response/responder.py`

Reviewed runtime configuration used by the responder:

```text
RESPONDER_BASE_URL=http://172.19.98.209:4000/v1
RESPONDER_MODEL=gpt-oss:20b
RESPONDER_PROVIDER=litellm
Responder credential: redacted; value not retained in audit evidence.
```

The secret value itself is intentionally not retained in audit evidence.

**Rationale:** Semgrep identified a generic dynamic-URL capability in the OpenAI-compatible adapter. Runtime configuration review confirmed that `RESPONDER_BASE_URL` is supplied through trusted responder process configuration and points to the operator-controlled local LiteLLM service on the private WSL network. The URL is not derived from TaskFlow incident evidence, model output, or attacker-controlled application input. The reviewed deployment path does not expose this configuration as user-controlled runtime data. Therefore the generic dynamic-URL pattern does not represent an SSRF/data-exfiltration finding in the reviewed P6-A scope.

**Boundary condition:** This disposition depends on the responder endpoint remaining operator-controlled. Introducing an externally supplied or runtime-derived responder URL would require a new security review of the endpoint-control boundary.

**Remediation status:** No remediation required for the reviewed configuration.

## Post-Remediation Verification

The original human dispositions for `SEC-SG-M4-ACTION-PINNING` and `SEC-SG-UV-COOLDOWN` remain `remediate`. This section records the subsequent verification result without changing the historical disposition record.

### Verification identity

```text
source_revision  = 7906eb5fbe3c75bb967926e048b28d4cbf912931
semgrep_version  = 1.179.0
scan_scope       = module-4 .github/workflows
exit_code        = 0
verification_ts  = 2026-10-07T10:34:04Z
```

Final Semgrep result summary:

```text
results                   = 19
WARNING                   = 18
MEDIUM                    = 1
m4_mutable_action_results = 0
uv_cooldown_results       = 0
```

The remaining 19 observations are the previously dispositioned M3/in-scope boundary, `workflow_run`, Bun release-age, and responder URL observations. No new M4 mutable-action or uv cooldown observation remains after remediation.

### Final evidence hashes

The final Semgrep evidence was recorded under:

```text
module-4/security-audit/runs/semgrep/p6-remediation-final/
```

The verification metadata records the immutable remediation checkpoint, scanner version, scan scope, exit code, and verification timestamp.

The final evidence files are:

```text
semgrep.json
run-metadata.txt
```

The earlier uv remediation verification remains retained under:

```text
module-4/security-audit/runs/semgrep/p6-remediation-uv/
```

### SEC-SG-M4-ACTION-PINNING — final disposition

**Original human disposition:** `remediate`

**Final remediation status:** `verified / closed`

Verification established:

- all affected M4 third-party GitHub Actions are pinned to verified full 40-character commit SHAs;
- `m4_mutable_action_results = 0` in the final Semgrep scan;
- the final scan completed successfully with exit code `0`.

### SEC-SG-UV-COOLDOWN — final disposition

**Original human disposition:** `remediate`

**Final remediation status:** `verified / closed`

Verification established:

```text
uv lock --check = success
uv sync --locked = success
uv_cooldown_results = 0
```

The remediation configuration is:

```toml
[tool.uv]
package = false
required-version = ">=0.9.17"
exclude-newer = "7 days"
```

The lockfile was regenerated under the seven-day cutoff and retains the resulting reproducibility metadata.

### Verification conclusion

Both P6-A remediation items that were assigned `remediate` have now been subsequently verified and closed. The accepted hardening gap and false-positive dispositions remain configuration- and scope-specific and are unchanged.

## Scanner limitations

Semgrep emitted parser/partial-parsing records for:

- `module-4/incident-response/runbooks/verify-recovery.sh`
- `module-4/deploy/ec2/deploy.sh`
- `module-4/deploy/ec2/user-data.sh`
- `.github/workflows/deploy-module-4.yml`
- `.github/workflows/promote-module-4.yml`

These are coverage limitations, not security findings.

## Review conclusion

The Semgrep output contains scanner observations, not automatically confirmed vulnerabilities. Human review has now recorded an explicit disposition for all six grouped observations:

- 1 group remediated and verified within P6-A (M4 Action pinning)
- 1 inherited/out-of-scope M3 baseline group
- 2 false positives (`workflow_run` checkout and responder dynamic URL)
- 1 accepted hardening gap (Bun release age)
- 1 group remediated and verified within P6-A (`uv` dependency cooldown)

The accepted and false-positive decisions are configuration- and scope-specific and must not be generalized beyond the reviewed implementation.
