"""Executable reference model for Causal-ABAC attack rejection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Control(str, Enum):
    ROOT_BINDING = "C1"
    NONCE_FRESH_HEAD = "C2"
    INTEGRITY_PROPAGATION = "C3"
    ENDORSEMENT_CHECKING = "C4"
    EXACT_ACTION_BINDING = "C5"
    CURRENT_REVOCATION = "C6"
    SUITE_BINDING = "C7"


ALL_CONTROLS = frozenset(Control)


@dataclass(frozen=True)
class AttackSpec:
    group: str
    attack_id: str
    name: str
    primary_control: Control
    rejecting_component: str


@dataclass(frozen=True)
class DecisionTrace:
    attack_id: str
    attempted: bool
    violated_control: str
    monitor_decision: str
    proof_result: str
    gateway_decision: str
    service_effect: bool
    reject_reason: str


ATTACKS = (
    AttackSpec("G1", "A1", "Direct prompt injection", Control.INTEGRITY_PROPAGATION, "Safe_P"),
    AttackSpec("G1", "A2", "Indirect retrieval injection", Control.INTEGRITY_PROPAGATION, "Safe_P"),
    AttackSpec("G1", "A3", "Malicious tool output", Control.INTEGRITY_PROPAGATION, "Safe_P"),
    AttackSpec("G1", "A4", "Compromised subagent", Control.INTEGRITY_PROPAGATION, "Safe_P/PrincipalOK"),
    AttackSpec("G1", "A5", "Provenance omission", Control.INTEGRITY_PROPAGATION, "TransitionsOK"),
    AttackSpec("G1", "A6", "Event reordering", Control.INTEGRITY_PROPAGATION, "TransitionsOK"),
    AttackSpec("G2", "A7", "Credential amalgamation", Control.ROOT_BINDING, "PrincipalOK"),
    AttackSpec("G2", "A8", "False two-agent independence", Control.ROOT_BINDING, "P_root"),
    AttackSpec("G2", "A9", "Delegation widening", Control.ROOT_BINDING, "DelegationOK"),
    AttackSpec("G3", "A10", "Request substitution", Control.EXACT_ACTION_BINDING, "Bind/H(q)"),
    AttackSpec("G3", "A11", "Replay", Control.NONCE_FRESH_HEAD, "Unused(nu)/Bind"),
    AttackSpec("G3", "A12", "Stale attestation or revocation", Control.CURRENT_REVOCATION, "RootBundleOK/RevOK"),
    AttackSpec("G3", "A13", "Suite downgrade", Control.SUITE_BINDING, "Bind/suiteID"),
)

ATTACK_BY_ID = {attack.attack_id: attack for attack in ATTACKS}


def evaluate_attack(
    attack_id: str,
    *,
    attempted: bool = True,
    active_controls: frozenset[Control] = ALL_CONTROLS,
    violated_control: Control | None = None,
) -> DecisionTrace:
    """Evaluate one attacker-selected protected effect.

    A non-attempted injection produces a benign request. An attempted attack is
    rejected when the relation control associated with the manipulated
    invariant is active. The gateway executes the attacker goal only if that
    control is absent.
    """
    attack = ATTACK_BY_ID[attack_id]
    control = violated_control or attack.primary_control
    if not attempted:
        return DecisionTrace(
            attack_id=attack_id,
            attempted=False,
            violated_control=control.value,
            monitor_decision="permit_benign",
            proof_result="valid_benign",
            gateway_decision="permit_benign",
            service_effect=False,
            reject_reason="attacker goal not selected",
        )
    if control in active_controls:
        monitor_stage = control in {
            Control.INTEGRITY_PROPAGATION,
            Control.ENDORSEMENT_CHECKING,
        }
        return DecisionTrace(
            attack_id=attack_id,
            attempted=True,
            violated_control=control.value,
            monitor_decision="reject" if monitor_stage else "record",
            proof_result="unsatisfied_relation",
            gateway_decision="reject",
            service_effect=False,
            reject_reason=attack.rejecting_component,
        )
    return DecisionTrace(
        attack_id=attack_id,
        attempted=True,
        violated_control=control.value,
        monitor_decision="permit",
        proof_result="valid_under_ablation",
        gateway_decision="permit",
        service_effect=True,
        reject_reason="control removed",
    )


def controls_without(control: Control | None) -> frozenset[Control]:
    """Return the full relation control set with one optional ablation."""
    if control is None:
        return ALL_CONTROLS
    return frozenset(candidate for candidate in ALL_CONTROLS if candidate != control)
