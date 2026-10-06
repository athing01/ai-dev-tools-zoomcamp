#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_OPERATION = "tasks.list"
EXPECTED_ENVIRONMENT = "dev"
EXPECTED_ALERT_UID = "taskflow-p4-tasks-list-failure"
EXPECTED_ACTION = "recover_task_list_dev_fault"
POLICY_NAME = "taskflow-p5-autonomy"


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        fail(f"refusing symbolic-link input: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON: {exc}")

    if not isinstance(data, dict):
        fail("JSON root must be an object")

    return data


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def validate_scope(response: dict[str, Any]) -> None:
    incident_id = response.get("incident_id")
    if not isinstance(incident_id, str) or not incident_id:
        fail("incident_id is missing")

    # Response schema is validated by responder.py.
    # This gate repeats only the immutable scope needed for policy evaluation.
    evidence_path = Path(response["_policy_evidence_path"])
    evidence = load_json(evidence_path)

    incident = evidence.get("incident")
    alert = evidence.get("alert")

    if not isinstance(incident, dict):
        fail("evidence.incident is missing")

    if incident.get("operation") != EXPECTED_OPERATION:
        fail("policy operation mismatch")

    if incident.get("environment") != EXPECTED_ENVIRONMENT:
        fail("policy environment mismatch")

    if not isinstance(alert, dict):
        fail("evidence.alert is missing")

    if alert.get("uid") != EXPECTED_ALERT_UID:
        fail("policy alert UID mismatch")

    evidence_incident_id = incident.get("incident_id")
    if evidence_incident_id != incident_id:
        fail("response/evidence incident_id mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="External policy boundary for TaskFlow P5 responder output"
    )
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    response = load_json(args.response)

    # Keep the evidence path outside model-controlled response data.
    response["_policy_evidence_path"] = str(args.evidence)

    validate_scope(response)

    proposed_action = response.get("proposed_action")
    escalation = response.get("escalation")

    if proposed_action is not None:
        if not isinstance(proposed_action, dict):
            fail("proposed_action must be an object or null")

        action_id = proposed_action.get("action_id")
        if action_id != EXPECTED_ACTION:
            fail(
                f"action is not allowlisted: {action_id!r}"
            )

        # This gate deliberately does NOT authorize an action.
        # Any proposed action requires human/manual authorization.
        decision = {
            "decision": "authorization_required",
            "action_authorized": False,
            "reason": (
                "A proposed bounded action requires external human/manual "
                "authorization before execution."
            ),
        }

        disposition = {
            "type": "authorization-required",
            "execution_permitted": False,
        }

    else:
        if not isinstance(escalation, dict):
            fail("escalation must be an object")

        if escalation.get("decision") != "escalate":
            fail(
                "no action was proposed but escalation.decision is not 'escalate'"
            )

        reason = escalation.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            fail("escalation.reason is required")

        decision = {
            "decision": "not_authorized",
            "action_authorized": False,
            "reason": reason,
        }

        disposition = {
            "type": "escalation",
            "execution_permitted": False,
        }

    incident_id = response["incident_id"]

    record = {
        "policy_version": "1",
        "policy_name": POLICY_NAME,
        "incident_id": incident_id,
        "recorded_at": utc_now(),
        "disposition": disposition,
        "authorization": decision,
        "proposed_action": proposed_action,
        "escalation": escalation,
        "provenance": {
            "responder_model": response["responder"]["model"],
            "responder_provider": response["responder"]["provider"],
            "responder_adapter": response["responder"]["adapter"],
            "responder_configuration_ref": response["responder"][
                "configuration_ref"
            ],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.output.exists() and args.output.is_symlink():
        fail("output must not be a symbolic link")

    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    encoded = (
        json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")

    try:
        temporary.write_bytes(encoded)
        os.chmod(temporary, 0o600)
        os.replace(temporary, args.output)
        os.chmod(args.output, 0o600)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        fail(f"cannot write decision record: {exc}")

    print(f"Policy decision written: {args.output}")
    print(f"Authorization decision: {decision['decision']}")
    print(f"Execution permitted: {decision['action_authorized']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
