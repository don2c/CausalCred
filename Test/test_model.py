from __future__ import annotations

import unittest

from causalcred_eval.model import ALL_CONTROLS, ATTACKS, controls_without, evaluate_attack


class ModelTests(unittest.TestCase):
    def test_full_relation_rejects_every_attack_family(self) -> None:
        for attack in ATTACKS:
            with self.subTest(attack=attack.attack_id):
                trace = evaluate_attack(attack.attack_id, active_controls=ALL_CONTROLS)
                self.assertFalse(trace.service_effect)
                self.assertEqual(trace.gateway_decision, "reject")

    def test_corresponding_ablation_reopens_path(self) -> None:
        for attack in ATTACKS:
            with self.subTest(attack=attack.attack_id):
                active = controls_without(attack.primary_control)
                trace = evaluate_attack(attack.attack_id, active_controls=active)
                self.assertTrue(trace.service_effect)
                self.assertEqual(trace.gateway_decision, "permit")

    def test_nonselected_injection_has_no_attacker_effect(self) -> None:
        trace = evaluate_attack("A1", attempted=False)
        self.assertFalse(trace.service_effect)
        self.assertEqual(trace.gateway_decision, "permit_benign")


if __name__ == "__main__":
    unittest.main()
