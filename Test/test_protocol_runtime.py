from __future__ import annotations

import unittest

from causalcred_eval.experiments import ABLATION_ATTACK
from causalcred_eval.model import ALL_CONTROLS, ATTACKS, Control, controls_without
from causalcred_eval.protocol import build_scenario, evaluate_scenario


class ProtocolRuntimeTests(unittest.TestCase):
    def test_all_registered_attacks_are_rejected_from_concrete_state(self) -> None:
        for attack in ATTACKS:
            with self.subTest(attack=attack.attack_id):
                scenario = build_scenario("cloud", attack.attack_id, f"test-{attack.attack_id}")
                trace = evaluate_scenario(scenario, active_controls=ALL_CONTROLS)
                self.assertFalse(trace.service_effect)
                self.assertEqual(trace.gateway_decision, "reject")
                self.assertNotEqual(trace.reject_reason, "none")

    def test_every_control_has_a_state_changing_mutation(self) -> None:
        for control in Control:
            attack_id = ABLATION_ATTACK[control]
            with self.subTest(control=control.value, attack=attack_id):
                scenario = build_scenario(
                    "supply_chain",
                    attack_id,
                    f"mutation-{control.value}",
                    target_control=control,
                )
                full = evaluate_scenario(scenario)
                ablated = evaluate_scenario(scenario, active_controls=controls_without(control))
                self.assertFalse(full.service_effect)
                self.assertTrue(ablated.service_effect)
                self.assertEqual(ablated.gateway_decision, "permit")

    def test_request_substitution_is_rejected_at_gateway(self) -> None:
        scenario = build_scenario("cloud", "A10", "request-binding")
        trace = evaluate_scenario(scenario)
        self.assertEqual(trace.monitor_decision, "record")
        self.assertEqual(trace.relation_decision, "satisfied")
        self.assertEqual(trace.proof_result, "valid_reference_proof")
        self.assertEqual(trace.gateway_decision, "reject")
        self.assertNotEqual(trace.request_digest, trace.forwarded_request_digest)

    def test_parent_omission_is_detected_before_proof(self) -> None:
        scenario = build_scenario("cloud", "A5", "parent-omission")
        trace = evaluate_scenario(scenario)
        self.assertEqual(trace.monitor_decision, "reject")
        self.assertEqual(trace.proof_result, "not_constructed")
        self.assertIn("parent-complete", trace.reject_reason)

    def test_benign_request_is_permitted_without_attacker_effect(self) -> None:
        scenario = build_scenario(
            "cloud", "A1", "benign-request", attacker_goal_selected=False
        )
        trace = evaluate_scenario(scenario)
        self.assertEqual(trace.gateway_decision, "permit_benign")
        self.assertFalse(trace.service_effect)


if __name__ == "__main__":
    unittest.main()
