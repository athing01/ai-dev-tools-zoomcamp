---
name: taskflow-api-review
description: Review proposed TaskFlow API or OpenAPI changes for backward compatibility, request and response schemas, status and error behavior, runtime-contract consistency, persistence implications, and regression-test coverage. Use when asked to review an API diff or contract.
---

# TaskFlow API Review

## Purpose

Perform a focused, evidence-based review of proposed TaskFlow HTTP API
changes. Identify contract incompatibilities, discrepancies between the
documented contract and implementation, behavioral risks, and missing
regression tests.

This skill is a review workflow, not an implementation workflow. It produces
review evidence and recommendations; it does not change the application.

## Inputs and scope

Establish these inputs before reviewing:

- **Proposed change:** a supplied diff, pull request diff, explicit base
  revision, or current repository changes.
- **API contract:** use the user-specified API contract. For this repository,
  the default is `module-3/openapi.yaml`.
- **Implementation sources:** the actual route handlers, request and response
  schemas, service or repository abstractions, and relevant persistence code.
- **Tests:** user-specified test locations or the existing tests relevant to
  the affected endpoints and behavior.
- **Constraints:** the requested review scope, relevant project instructions,
  and any explicit compatibility requirements.

Do not invent a base revision, proposed change, endpoint, schema, test, or
product requirement.

If reviewing a proposed change and no diff or changed files can be established,
report that no proposed change was available and stop. Ask for the missing diff
or base revision rather than presenting a baseline inspection as a change review.

If the user requests a baseline audit rather than a change review, state that
scope explicitly and proceed with a baseline audit.

## Mandatory boundaries

1. Read the root `AGENTS.md` and `module-3/AGENTS.md` before inspecting
   implementation details. Follow all applicable, higher-priority product
   specifications and implementation decisions.
2. Keep the review within the requested scope. Read the smallest useful set of
   repository files needed to establish evidence.
3. Use available read-only file, diff, search, and inspection tools. This
   workflow is tool-agnostic: do not assume a particular editor, shell,
   model, plugin, or MCP server is available.
4. Do not edit files, apply patches, create commits, change configuration,
   install dependencies, or perform application mutations.
5. Do not deploy, invoke deployment commands, access AWS, inspect credentials
   or secrets, or contact production services or endpoints.
6. Do not assume that read-only instructions enforce permissions. Report the
   effective permission mode only when the active session provides evidence
   for it. Do not claim that read-only mode disables shell use or outbound
   network access.
7. A review recommendation is not authorization to merge, release, or deploy.

## Review procedure

### 1. Establish review scope

- Identify the requested endpoints, proposed changes, base revision, API
  contract, and relevant test locations.
- Inspect the working-tree and supplied diff using available read-only tools.
- Distinguish staged, unstaged, and committed changes when that distinction
  affects the requested comparison.
- Identify which paths and symbols are actually in scope.
- If the diff is empty or its base cannot be resolved, report the limitation
  and stop when it prevents a valid change review.

Never silently substitute an unrelated revision or broaden a targeted review
to the whole repository.

### 2. Read authoritative guidance

Read the root `AGENTS.md` and `module-3/AGENTS.md`. Consult the applicable
Module 3 product specification and implementation plan when needed.

Treat these documents as constraints, not as evidence that implementation
behavior exists. Verify behavioral claims against source code and tests.

If the proposed change conflicts with an authoritative requirement, identify
the conflict and stop short of inventing a resolution.

### 3. Trace the API contract and implementation

Inspect the relevant portions of the API contract, route handlers, validation
schemas, service/repository abstractions, persistence code, and existing tests.

For each affected operation, compare the proposed and current behavior:

- HTTP method, path, path parameters, and operation identifier;
- request-body and parameter requirements, types, constraints, defaults,
  nullability, enums, and unknown-property behavior;
- response status codes, response schemas, headers, and error representations;
- identifier semantics, validation rules, and missing-resource behavior;
- runtime behavior and the documented contract;
- repository or persistence implications, including migration compatibility
  when the affected implementation provides evidence of such an impact;
- compatibility with existing clients and existing tests.

Pay particular attention to removed or renamed endpoints, newly required
request fields, tightened validation, changed enum values, removed response
fields, altered status codes, and changed error semantics.

Do not infer actual runtime behavior solely from OpenAPI descriptions. Trace
the implementation or mark the behavior as unverified.

### 4. Evaluate compatibility and risks

For each potential issue:

- State the observed behavior or contract change.
- Cite the exact file path and line number, symbol, operation, or schema.
- Explain the effect on clients, runtime behavior, or data compatibility.
- Distinguish direct evidence from inference.
- State the severity and confidence, with a rationale.
- Recommend a bounded corrective action or a concrete regression test.

Consider both breaking and non-breaking changes. Do not call a change breaking
unless the affected client or contract assumption is supported by evidence.

A missing test is a coverage gap, not proof of a runtime defect. A missing
OpenAPI response declaration is a contract finding only when supported by
the relevant contract and implementation evidence.

### 5. Recommend regression tests

Recommend focused tests that correspond to identified risks. Consider:

- successful requests and responses;
- invalid parameters and request bodies;
- required fields, whitespace constraints, enums, and extra properties;
- unknown resource identifiers and error responses;
- backward compatibility of existing response fields;
- contract-to-runtime consistency;
- repository behavior and persistence implications, where relevant.

Prefer the existing project test conventions and the smallest useful test set.

Do not run test commands by default. Running tests can create caches, require
services, or have side effects. If the user explicitly requests execution,
first establish which tests are safe and bounded in the current environment.
Otherwise, provide the suggested test targets without claiming they passed.

## Required output

Use the following headings in every completed review.

# TaskFlow API Review

## 1. Scope and Inputs

State the diff or baseline reviewed, base revision if known, affected paths and
operations, contract path, implementation sources, and test locations examined.
List important inputs that were unavailable.

## 2. Executive Summary

Give a concise overall assessment. Separate confirmed defects, compatibility
risks, test gaps, and unresolved questions.

## 3. Findings

List findings by severity: Critical, High, Medium, Low, or Informational.

For every finding include:

- **ID and severity**
- **Confidence:** High, Medium, or Low
- **Evidence:** exact repository path and line, symbol, operation, or schema
- **Verified facts:** what the inspected source or contract directly shows
- **Risk or impact:** what could happen and under which conditions
- **Recommendation:** the bounded change or test that would address the risk

Avoid duplicate findings. Do not assign high severity merely because a
possible issue exists.

If no findings are confirmed, state "No confirmed findings within the
reviewed scope." Describe the coverage and limitations; do not claim that the
entire API is defect-free.

## 4. Breaking-Change Assessment

Summarize confirmed breaking changes, possible breaking changes, compatible
changes, and any areas where available evidence is insufficient. Explain the
client-facing consequences of each confirmed or plausible change.

## 5. Recommended Tests

List the most valuable focused regression tests, linking each recommendation
to the finding or behavior it covers. Clearly distinguish recommended tests
from tests actually executed.

## 6. Evidence Gaps and Stop Conditions

Record missing diffs, unresolved base revisions, inaccessible implementation
sources, unverified runtime behavior, unavailable test evidence, and conflicts
with authoritative instructions.

State when incomplete evidence limits the review. Do not conceal an
inconclusive result behind a confident summary.

## Final review rules

- Be specific, reproducible, and evidence-based.
- Separate facts, inferences, and recommendations.
- Do not invent file references, test outcomes, runtime behavior, or approvals.
- Do not treat model confidence as evidence.
- Do not modify the repository.
