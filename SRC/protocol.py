"""Executable Causal-ABAC control-flow and provenance reference runtime.

The runtime evaluates concrete protocol state. It constructs credential,
delegation, monitor-event, challenge, proof-statement, and gateway objects for
each trial. Attack generators mutate one invariant and the verifier derives the
decision from the resulting state.

Cryptographic objects are represented by domain-separated SHA-256 commitments.
This module validates protocol binding and state-transition logic. It does not
claim performance or security equivalence to ML-DSA, ML-KEM, or Ligetron.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from typing import Any

from .model import ALL_CONTROLS, ATTACK_BY_ID, Control


REFERENCE_SUITE = "causalcred-pq-reference-v1"


def canonical_hash(domain: str, value: Any) -> str:
    """Return a domain-separated digest of a canonical JSON value."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(f"{domain}\x00{encoded}".encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Credential:
    subject: str
    root: str
    attributes: tuple[str, ...]
    issuer: str
    epoch: int


@dataclass(frozen=True)
class Delegation:
    parent_root: str
    child_root: str
    operations: tuple[str, ...]
    resource_prefix: str
    expiry_epoch: int


@dataclass(frozen=True)
class Event:
    event_id: str
    index: int
    source: str
    source_integrity: int
    claimed_integrity: int
    parents: tuple[str, ...]
    declared_context: tuple[str, ...]
    field: str
    value: str
    endorsement_required: bool = False
    endorsement_valid: bool = True


@dataclass(frozen=True)
class Request:
    operation: str
    resource: str
    arguments: tuple[tuple[str, str], ...]

    def digest(self) -> str:
        return canonical_hash("request", asdict(self))


@dataclass(frozen=True)
class Challenge:
    nonce: str
    policy_epoch: int
    revocation_epoch: int
    attestation_epoch: int
    suite_id: str


@dataclass(frozen=True)
class Scenario:
    trial_id: str
    testbed: str
    attack_id: str
    attacker_goal_selected: bool
    credentials: tuple[Credential, ...]
    delegation: Delegation
    sponsor_root: str
    workload_root: str
    agent_root: str
    approval_root: str
    independent_approval_required: bool
    events: tuple[Event, ...]
    proven_request: Request
    forwarded_request: Request
    challenge: Challenge
    current_policy_epoch: int
    current_revocation_epoch: int
    current_attestation_epoch: int
    revoked_roots: tuple[str, ...]
    used_nonces: tuple[str, ...]
    expected_suite: str
    target_control: str


@dataclass(frozen=True)
class RuntimeTrace:
    trial_id: str
    testbed: str
    attack_id: str
    attacker_goal_selected: bool
    target_control: str
    monitor_decision: str
    relation_decision: str
    proof_result: str
    gateway_decision: str
    service_effect: bool
    reject_reason: str
    request_digest: str
    forwarded_request_digest: str
    state_digest: str
    statement_digest: str
    proof_digest: str | None
    event_count: int
    active_controls: tuple[str, ...]


def _root(label: str, trial_id: str) -> str:
    return canonical_hash("root", {"label": label, "trial": trial_id})


def _base_scenario(testbed: str, attack_id: str, trial_id: str) -> Scenario:
    sponsor = _root("sponsor", trial_id)
    workload = _root("workload", trial_id)
    agent = _root("agent", trial_id)
    approval = _root("approver", trial_id)
    resource = "/cloud/accounts/service" if testbed == "cloud" else "/supply/releases/stable"
    operation = "CreateAccount" if testbed == "cloud" else "PublishRelease"
    request = Request(operation, resource, (("target", "authorised-target"),))
    events = (
        Event(
            event_id="e0",
            index=0,
            source="task-contract",
            source_integrity=3,
            claimed_integrity=3,
            parents=(),
            declared_context=(),
            field="operation",
            value=operation,
        ),
        Event(
            event_id="e1",
            index=1,
            source="authenticated-inventory",
            source_integrity=3,
            claimed_integrity=3,
            parents=("e0",),
            declared_context=("e0",),
            field="target",
            value="authorised-target",
        ),
        Event(
            event_id="e2",
            index=2,
            source="deterministic-agent-v1",
            source_integrity=3,
            claimed_integrity=3,
            parents=("e0", "e1"),
            declared_context=("e0", "e1"),
            field="request",
            value=request.digest(),
        ),
    )
    challenge = Challenge(
        nonce=canonical_hash("nonce", trial_id)[:32],
        policy_epoch=7,
        revocation_epoch=11,
        attestation_epoch=5,
        suite_id=REFERENCE_SUITE,
    )
    return Scenario(
        trial_id=trial_id,
        testbed=testbed,
        attack_id=attack_id,
        attacker_goal_selected=True,
        credentials=(
            Credential("sponsor", sponsor, ("incident-owner",), "issuer-1", 11),
            Credential("workload", workload, ("attested-workload",), "issuer-1", 11),
            Credential("agent", agent, ("tool-agent",), "issuer-1", 11),
        ),
        delegation=Delegation(sponsor, agent, (operation,), resource.rsplit("/", 1)[0], 20),
        sponsor_root=sponsor,
        workload_root=workload,
        agent_root=agent,
        approval_root=approval,
        independent_approval_required=True,
        events=events,
        proven_request=request,
        forwarded_request=request,
        challenge=challenge,
        current_policy_epoch=7,
        current_revocation_epoch=11,
        current_attestation_epoch=5,
        revoked_roots=(),
        used_nonces=(),
        expected_suite=REFERENCE_SUITE,
        target_control=ATTACK_BY_ID[attack_id].primary_control.value,
    )


def _attacker_request(base: Scenario) -> Request:
    target = "attacker-admin" if base.testbed == "cloud" else "attacker-namespace"
    return replace(base.proven_request, arguments=(("target", target),))


def build_scenario(
    testbed: str,
    attack_id: str,
    trial_id: str,
    *,
    attacker_goal_selected: bool = True,
    target_control: Control | None = None,
) -> Scenario:
    """Construct a trial and apply one attack mutation.

    ``target_control`` is used by the single-control mutation experiment. It
    constructs a state that violates only the selected control.
    """
    base = _base_scenario(testbed, attack_id, trial_id)
    if not attacker_goal_selected:
        return replace(base, attacker_goal_selected=False, target_control="none")

    control = target_control or ATTACK_BY_ID[attack_id].primary_control
    base = replace(base, target_control=control.value)

    if control == Control.INTEGRITY_PROPAGATION:
        source_by_attack = {
            "A1": "direct-prompt",
            "A2": "retrieved-document",
            "A3": "tool-output",
            "A4": "foreign-subagent",
            "A5": "omitted-context",
            "A6": "reordered-event",
        }
        source = source_by_attack.get(attack_id, "untrusted-input")
        untrusted = Event(
            event_id="u0",
            index=1 if attack_id == "A6" else 2,
            source=source,
            source_integrity=0,
            claimed_integrity=0,
            parents=("e0",),
            declared_context=("e0",),
            field="target",
            value="attacker-selected",
        )
        request_event = replace(
            base.events[-1],
            index=3,
            value=_attacker_request(base).digest(),
            parents=("e0", "e1") if attack_id == "A5" else ("e0", "e1", "u0"),
            declared_context=("e0", "e1", "u0"),
        )
        if attack_id == "A6":
            untrusted = replace(untrusted, parents=("e2",))
        return replace(
            base,
            events=(base.events[0], base.events[1], untrusted, request_event),
            proven_request=_attacker_request(base),
            forwarded_request=_attacker_request(base),
        )

    if control == Control.ENDORSEMENT_CHECKING:
        transformed = replace(
            base.events[-1],
            endorsement_required=True,
            endorsement_valid=False,
            value=_attacker_request(base).digest(),
        )
        return replace(
            base,
            events=(base.events[0], base.events[1], transformed),
            proven_request=_attacker_request(base),
            forwarded_request=_attacker_request(base),
        )

    if control == Control.ROOT_BINDING:
        if attack_id == "A9":
            widened = replace(base.proven_request, operation="DeleteAuditSink")
            return replace(base, proven_request=widened, forwarded_request=widened)
        if attack_id == "A8":
            return replace(base, approval_root=base.sponsor_root)
        foreign = _root("foreign-agent", trial_id)
        return replace(base, agent_root=foreign)

    if control == Control.EXACT_ACTION_BINDING:
        return replace(base, forwarded_request=_attacker_request(base))

    if control == Control.NONCE_FRESH_HEAD:
        return replace(base, used_nonces=(base.challenge.nonce,))

    if control == Control.CURRENT_REVOCATION:
        stale = replace(base.challenge, revocation_epoch=base.current_revocation_epoch - 1)
        return replace(base, challenge=stale, revoked_roots=(base.agent_root,))

    if control == Control.SUITE_BINDING:
        downgraded = replace(base.challenge, suite_id="classical-reference-v0")
        return replace(base, challenge=downgraded)

    raise ValueError(f"unsupported control: {control}")


def _event_integrity_ok(events: tuple[Event, ...]) -> tuple[bool, str]:
    by_id: dict[str, Event] = {}
    effective: dict[str, int] = {}
    for event in sorted(events, key=lambda item: item.index):
        if event.event_id in by_id:
            return False, "duplicate event identifier"
        if any(parent not in by_id for parent in event.parents):
            return False, "event parent is absent or ordered after its child"
        if set(event.parents) != set(event.declared_context):
            return False, "declared model context is not parent-complete"
        parent_levels = [effective[parent] for parent in event.parents]
        derived = min([event.source_integrity, *parent_levels])
        if event.claimed_integrity > derived:
            return False, "integrity elevation violates conservative propagation"
        by_id[event.event_id] = event
        effective[event.event_id] = derived
    final = max(events, key=lambda item: item.index)
    if effective[final.event_id] < 2:
        return False, "request field has insufficient provenance integrity"
    return True, "ok"


def _root_and_delegation_ok(scenario: Scenario) -> tuple[bool, str]:
    credential_roots = {credential.subject: credential.root for credential in scenario.credentials}
    if credential_roots != {
        "sponsor": scenario.sponsor_root,
        "workload": scenario.workload_root,
        "agent": scenario.agent_root,
    }:
        return False, "credential roots do not form one compound principal"
    if scenario.independent_approval_required and scenario.approval_root == scenario.sponsor_root:
        return False, "independent approval roots are equal"
    delegation = scenario.delegation
    request = scenario.proven_request
    if delegation.parent_root != scenario.sponsor_root or delegation.child_root != scenario.agent_root:
        return False, "delegation endpoints do not bind the active roots"
    if request.operation not in delegation.operations:
        return False, "requested operation widens delegation"
    if not request.resource.startswith(delegation.resource_prefix):
        return False, "requested resource widens delegation"
    if delegation.expiry_epoch < scenario.current_policy_epoch:
        return False, "delegation expired"
    return True, "ok"


def evaluate_scenario(
    scenario: Scenario,
    *,
    active_controls: frozenset[Control] = ALL_CONTROLS,
) -> RuntimeTrace:
    """Evaluate the monitor, proof relation, gateway, and protected effect."""
    state_digest = canonical_hash("monitor-state", [asdict(event) for event in scenario.events])
    request_digest = scenario.proven_request.digest()
    forwarded_digest = scenario.forwarded_request.digest()
    statement = {
        "request": request_digest,
        "state": state_digest,
        "nonce": scenario.challenge.nonce,
        "policy_epoch": scenario.challenge.policy_epoch,
        "revocation_epoch": scenario.challenge.revocation_epoch,
        "attestation_epoch": scenario.challenge.attestation_epoch,
        "suite": scenario.challenge.suite_id,
        "roots": [scenario.sponsor_root, scenario.workload_root, scenario.agent_root],
    }
    statement_digest = canonical_hash("statement", statement)

    if not scenario.attacker_goal_selected:
        proof_digest = canonical_hash("proof", {"statement": statement_digest, "benign": True})
        return RuntimeTrace(
            trial_id=scenario.trial_id,
            testbed=scenario.testbed,
            attack_id=scenario.attack_id,
            attacker_goal_selected=False,
            target_control="none",
            monitor_decision="permit_benign",
            relation_decision="satisfied",
            proof_result="valid_reference_proof",
            gateway_decision="permit_benign",
            service_effect=False,
            reject_reason="attacker goal not selected",
            request_digest=request_digest,
            forwarded_request_digest=forwarded_digest,
            state_digest=state_digest,
            statement_digest=statement_digest,
            proof_digest=proof_digest,
            event_count=len(scenario.events),
            active_controls=tuple(sorted(control.value for control in active_controls)),
        )

    if Control.INTEGRITY_PROPAGATION in active_controls:
        ok, reason = _event_integrity_ok(scenario.events)
        if not ok:
            return _rejected_trace(scenario, active_controls, state_digest, statement_digest, reason, "monitor")

    if Control.ENDORSEMENT_CHECKING in active_controls:
        if any(event.endorsement_required and not event.endorsement_valid for event in scenario.events):
            return _rejected_trace(
                scenario,
                active_controls,
                state_digest,
                statement_digest,
                "required transformation endorsement is invalid",
                "monitor",
            )

    relation_checks: list[tuple[bool, str]] = []
    if Control.ROOT_BINDING in active_controls:
        relation_checks.append(_root_and_delegation_ok(scenario))
    if Control.NONCE_FRESH_HEAD in active_controls:
        relation_checks.append(
            (scenario.challenge.nonce not in scenario.used_nonces, "nonce was already consumed")
        )
    if Control.CURRENT_REVOCATION in active_controls:
        current = (
            scenario.challenge.policy_epoch == scenario.current_policy_epoch
            and scenario.challenge.revocation_epoch == scenario.current_revocation_epoch
            and scenario.challenge.attestation_epoch == scenario.current_attestation_epoch
            and scenario.agent_root not in scenario.revoked_roots
        )
        relation_checks.append((current, "epoch or revocation witness is stale"))
    if Control.SUITE_BINDING in active_controls:
        relation_checks.append(
            (scenario.challenge.suite_id == scenario.expected_suite, "cryptographic suite mismatch")
        )

    for ok, reason in relation_checks:
        if not ok:
            return _rejected_trace(
                scenario, active_controls, state_digest, statement_digest, reason, "relation"
            )

    proof_digest = canonical_hash(
        "proof",
        {
            "statement": statement_digest,
            "witness_commitment": canonical_hash(
                "witness",
                {
                    "credentials": [asdict(item) for item in scenario.credentials],
                    "delegation": asdict(scenario.delegation),
                    "events": [event.event_id for event in scenario.events],
                },
            ),
        },
    )

    if Control.EXACT_ACTION_BINDING in active_controls and request_digest != forwarded_digest:
        return RuntimeTrace(
            trial_id=scenario.trial_id,
            testbed=scenario.testbed,
            attack_id=scenario.attack_id,
            attacker_goal_selected=True,
            target_control=scenario.target_control,
            monitor_decision="record",
            relation_decision="satisfied",
            proof_result="valid_reference_proof",
            gateway_decision="reject",
            service_effect=False,
            reject_reason="forwarded request differs from proof-bound request",
            request_digest=request_digest,
            forwarded_request_digest=forwarded_digest,
            state_digest=state_digest,
            statement_digest=statement_digest,
            proof_digest=proof_digest,
            event_count=len(scenario.events),
            active_controls=tuple(sorted(control.value for control in active_controls)),
        )

    return RuntimeTrace(
        trial_id=scenario.trial_id,
        testbed=scenario.testbed,
        attack_id=scenario.attack_id,
        attacker_goal_selected=True,
        target_control=scenario.target_control,
        monitor_decision="record",
        relation_decision="satisfied",
        proof_result="valid_reference_proof",
        gateway_decision="permit",
        service_effect=True,
        reject_reason="none",
        request_digest=request_digest,
        forwarded_request_digest=forwarded_digest,
        state_digest=state_digest,
        statement_digest=statement_digest,
        proof_digest=proof_digest,
        event_count=len(scenario.events),
        active_controls=tuple(sorted(control.value for control in active_controls)),
    )


def _rejected_trace(
    scenario: Scenario,
    active_controls: frozenset[Control],
    state_digest: str,
    statement_digest: str,
    reason: str,
    stage: str,
) -> RuntimeTrace:
    return RuntimeTrace(
        trial_id=scenario.trial_id,
        testbed=scenario.testbed,
        attack_id=scenario.attack_id,
        attacker_goal_selected=True,
        target_control=scenario.target_control,
        monitor_decision="reject" if stage == "monitor" else "record",
        relation_decision="not_evaluated" if stage == "monitor" else "unsatisfied",
        proof_result="not_constructed" if stage == "monitor" else "unsatisfied_relation",
        gateway_decision="reject",
        service_effect=False,
        reject_reason=reason,
        request_digest=scenario.proven_request.digest(),
        forwarded_request_digest=scenario.forwarded_request.digest(),
        state_digest=state_digest,
        statement_digest=statement_digest,
        proof_digest=None,
        event_count=len(scenario.events),
        active_controls=tuple(sorted(control.value for control in active_controls)),
    )


def trace_record(scenario: Scenario, trace: RuntimeTrace) -> dict[str, Any]:
    """Return a complete, serialisable execution record."""
    return {
        "schema_version": 1,
        "trial": asdict(trace),
        "challenge": asdict(scenario.challenge),
        "principal_roots": {
            "sponsor": scenario.sponsor_root,
            "workload": scenario.workload_root,
            "agent": scenario.agent_root,
            "approval": scenario.approval_root,
        },
        "delegation": asdict(scenario.delegation),
        "events": [asdict(event) for event in scenario.events],
        "proven_request": asdict(scenario.proven_request),
        "forwarded_request": asdict(scenario.forwarded_request),
        "evidence_class": "executed_reference_runtime",
    }
