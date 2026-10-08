# Module 4 P6-A — Scanner Runbook

## Purpose

Provide reproducible commands for the required security scanners after the P6 branch is created in the real TaskFlow repository.

Scanner output is evidence only. A scanner result becomes a confirmed finding only after source/context review and explicit human disposition.

## 1. Preconditions

Run all commands from the repository root:

```text
ai-dev-tools-zoomcamp/
```

Verify the checkout before running the scanner:

```bash
git rev-parse --show-toplevel
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

For the initial P6-A repository reference, the source baseline is the immutable merge commit:

```text
fba6a3945b0b59069580a2e2df6423f2503eb7eb
```

Record the exact commit actually scanned for every scanner run; do not substitute the incident runtime release SHA for the source revision.

## 2. Semgrep

Semgrep's current Community Edition documentation supports a local CLI scan using `semgrep --config=auto`. citeturn682852search0

Recommended bounded P6-A scope:

```bash
mkdir -p module-4/security-audit/runs/semgrep

semgrep --config=auto \
  --json \
  --output module-4/security-audit/runs/semgrep/semgrep.json \
  module-4 .github/workflows

semgrep --config=auto \
  module-4 .github/workflows \
  > module-4/security-audit/runs/semgrep/semgrep.txt 2>&1
```

Also record:

```bash
semgrep --version \
  > module-4/security-audit/runs/semgrep/version.txt
```

The P6 review should retain the raw JSON and human-readable result together with the commit SHA and timestamp.

### 3. Snyk Agent Scan

Current Snyk Agent Scan documentation describes scanning AI-agent components such as MCP servers, tools, prompts, resources, and skills. It supports scanning a specific agent-skill file and JSON output. citeturn749929view0turn749929view1turn749929view2

The TaskFlow responder is a custom Python responder rather than a packaged agent skill. Therefore the audit must not claim that scanning an arbitrary Python file is equivalent to a full Snyk Agent Scan.

The closest source-defined responder attack surface is the responder task/prompt boundary:

```text
module-4/incident-response/responder-task.md
```

A best-effort targeted scan can therefore be run as:

```bash
mkdir -p module-4/security-audit/runs/snyk-agent-scan

export SNYK_TOKEN='…'

uvx snyk-agent-scan@latest \
  scan module-4/incident-response/responder-task.md \
  --json \
  > module-4/security-audit/runs/snyk-agent-scan/responder-task.json
```

Snyk documents `SNYK_TOKEN` as the authentication mechanism for CLI use and supports a single skill-file target. citeturn749929view0

Record the installed scanner version and the exact command. Do not expose `SNYK_TOKEN` in repository evidence.

### Scope limitation

This targeted scan covers the responder task/prompt surface only. It does **not** by itself prove security of:

- `responder.py` adapter code;
- `policy-gate.py`;
- `autonomy-policy.yaml`;
- the fixed executor;
- GitHub OIDC/IAM;
- Docker capability;
- runtime credential handling.

Those surfaces remain subject to source review, Semgrep, configuration/IAM review, and human disposition.

## 4. Evidence handling

For each scanner run retain:

```text
scanner/version
command/configuration
source revision
scope
UTC timestamp
raw result
human review/disposition linkage
```

Do not copy API tokens, private keys, session credentials, or complete secret-bearing environment dumps into audit artifacts.

## 5. Interpretation rule

```text
scanner result
    ↓
source/runtime context review
    ↓
model-assisted review (analysis aid)
    ↓
human validation
    ↓
human disposition
    ↓
confirmed finding / false positive / observation / further evidence
```
