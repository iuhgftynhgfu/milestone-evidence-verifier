"""Milestone Evidence Verifier — validator + end-to-end tests (stdlib unittest).

Covers the independent re-evaluation validator: opposite assessments must
NOT both pass, agreement passes, review-class labels agree with each
other, broken validator output disagrees, structural checks are retained,
and full compute() runs store on agreement and store nothing on
disagreement. The stub's exec_prompt is scripted, so every scenario is
deterministic and needs no runtime, wallet, or paid service.

Run from the repository root: python -m unittest -v tests.test_milestone_validator
"""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_TESTS = os.path.dirname(os.path.abspath(__file__))
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)

import genlayer_stub

stub = genlayer_stub.install()

from contracts.milestone_contract import (
    MilestoneEvidenceVerifier,
    _decide,
    _validator_fn,
)

CLAIM = "Milestone: 1,000 active users in the first month"
EVIDENCE = "Analytics dashboard export: 1,024 monthly active users, 31 days after launch."
QUOTE = "1,024 monthly active users"


def _leader_result(support, relevance, found, decision=None, key_present=True, explanation=""):
    """Build a leader result dict, deriving the decision unless overridden."""
    if decision is None:
        decision = _decide(support, relevance, found)
    return {
        "claim_support": support,
        "metric_relevance": relevance,
        "metric_found": found,
        "explanation": explanation,
        "decision": decision,
        "key_figure_present": key_present,
    }


def _llm_response(support, relevance, found, explanation=""):
    """Build a scripted exec_prompt response (evidence fields only)."""
    return {
        "claim_support": support,
        "metric_relevance": relevance,
        "metric_found": found,
        "explanation": explanation,
    }


class TestValidator(unittest.TestCase):
    """Direct validator tests with a hand-crafted leader result."""

    def setUp(self):
        stub.reset()

    def _validate(self, leader_data, validator_response, key_present=True):
        if validator_response is not None:
            stub.queue_responses([validator_response])
        return _validator_fn(
            stub.vm.Return(leader_data), CLAIM, EVIDENCE, QUOTE, key_present
        )

    # -- 1. Opposite assessments must NOT both pass --

    def test_opposite_supported_leader_contradicted_validator(self):
        leader = _leader_result("supported", "relevant", True)
        validator = _llm_response("contradicted", "relevant", True)
        self.assertFalse(self._validate(leader, validator))

    def test_opposite_contradicted_leader_supported_validator(self):
        leader = _leader_result("contradicted", "relevant", True)
        validator = _llm_response("supported", "relevant", True)
        self.assertFalse(self._validate(leader, validator))

    # -- 2. Agreement passes --

    def test_agreement_accept(self):
        leader = _leader_result("supported", "relevant", True)
        validator = _llm_response("supported", "relevant", True)
        self.assertTrue(self._validate(leader, validator))

    def test_agreement_reject(self):
        leader = _leader_result("contradicted", "relevant", True)
        validator = _llm_response("contradicted", "relevant", True)
        self.assertTrue(self._validate(leader, validator))

    def test_agreement_reject_irrelevant(self):
        leader = _leader_result("partial", "irrelevant", True)
        validator = _llm_response("partial", "irrelevant", True)
        self.assertTrue(self._validate(leader, validator))

    # -- 3. Review-class equivalence --

    def test_review_class_partial_vs_insufficient(self):
        leader = _leader_result("partial", "relevant", True)
        validator = _llm_response("insufficient", "relevant", True)
        self.assertTrue(self._validate(leader, validator))

    def test_review_class_insufficient_vs_ambiguous(self):
        leader = _leader_result("insufficient", "relevant", True)
        validator = _llm_response("ambiguous", "uncertain", False)
        self.assertTrue(self._validate(leader, validator))

    def test_review_vs_decisive_disagrees(self):
        leader = _leader_result("partial", "relevant", True)
        validator = _llm_response("supported", "relevant", True)
        self.assertFalse(self._validate(leader, validator))

    def test_supported_review_vs_partial_review_disagrees(self):
        """Both derive review, but `supported` is not in the review class."""
        leader = _leader_result("supported", "relevant", False)
        validator = _llm_response("partial", "relevant", True)
        self.assertFalse(self._validate(leader, validator))

    # -- 4. Broken validator output disagrees --

    def test_validator_malformed_json(self):
        leader = _leader_result("supported", "relevant", True)
        self.assertFalse(self._validate(leader, "not json at all {{{"))

    def test_validator_missing_field(self):
        leader = _leader_result("supported", "relevant", True)
        broken = {"claim_support": "supported", "metric_relevance": "relevant"}
        self.assertFalse(self._validate(leader, broken))

    def test_validator_invalid_enum(self):
        leader = _leader_result("supported", "relevant", True)
        broken = _llm_response("definitely", "relevant", True)
        self.assertFalse(self._validate(leader, broken))

    # -- 5. Structural checks retained --

    def test_leader_decision_inconsistent_with_table(self):
        leader = _leader_result("supported", "relevant", True, decision="reject")
        validator = _llm_response("supported", "relevant", True)
        self.assertFalse(self._validate(leader, validator))
        self.assertEqual(stub.PROMPTS, [])

    def test_key_figure_present_mismatch(self):
        leader = _leader_result("supported", "relevant", True, key_present=False)
        validator = _llm_response("supported", "relevant", True)
        self.assertFalse(self._validate(leader, validator, key_present=True))

    def test_leader_result_not_a_return(self):
        leader = _leader_result("supported", "relevant", True)
        validator = _llm_response("supported", "relevant", True)
        stub.queue_responses([validator])
        self.assertFalse(_validator_fn(leader, CLAIM, EVIDENCE, QUOTE, True))

    def test_leader_supported_without_metric_found(self):
        leader = _leader_result("supported", "relevant", False)
        self.assertEqual(leader["decision"], "review")
        validator = _llm_response("supported", "relevant", False)
        self.assertFalse(self._validate(leader, validator))

    def test_leader_missing_key_figure_present(self):
        leader = _leader_result("supported", "relevant", True)
        del leader["key_figure_present"]
        validator = _llm_response("supported", "relevant", True)
        self.assertFalse(self._validate(leader, validator))


class TestDecisionTable(unittest.TestCase):
    """Direct decision-table rows."""

    def test_accept_row(self):
        self.assertEqual(_decide("supported", "relevant", True), "accept")

    def test_reject_contradicted(self):
        self.assertEqual(_decide("contradicted", "relevant", True), "reject")

    def test_reject_irrelevant(self):
        self.assertEqual(_decide("supported", "irrelevant", True), "reject")

    def test_review_supported_no_metric(self):
        self.assertEqual(_decide("supported", "relevant", False), "review")

    def test_review_partial(self):
        self.assertEqual(_decide("partial", "relevant", True), "review")


class TestEndToEnd(unittest.TestCase):
    """Full compute() runs through the stubbed run_nondet_unsafe."""

    def setUp(self):
        stub.reset()
        self.contract = MilestoneEvidenceVerifier()

    def _compute(self):
        return self.contract.compute("MS-001", CLAIM, EVIDENCE, QUOTE)

    def test_agreement_stores_evaluation(self):
        stub.queue_responses([
            _llm_response("supported", "relevant", True),
            _llm_response("supported", "relevant", True),
        ])
        result = self._compute()
        self.assertEqual(result["decision"], "accept")
        self.assertEqual(result["claim_support"], "supported")
        self.assertTrue(result["key_figure_present"])
        self.assertTrue(result["evaluation_complete"])
        self.assertFalse(result["review_required"])
        self.assertEqual(self.contract.get_evaluation("MS-001"), result)

    def test_leader_and_validator_prompts_identical(self):
        stub.queue_responses([
            _llm_response("supported", "relevant", True),
            _llm_response("supported", "relevant", True),
        ])
        self._compute()
        self.assertEqual(len(stub.PROMPTS), 2)
        self.assertEqual(stub.PROMPTS[0], stub.PROMPTS[1])

    def test_disagreement_stores_nothing(self):
        stub.queue_responses([
            _llm_response("supported", "relevant", True),
            _llm_response("contradicted", "relevant", True),
        ])
        with self.assertRaises(stub.vm.UserError):
            self._compute()
        self.assertIsNone(self.contract.get_evaluation("MS-001"))

    def test_review_class_agreement_end_to_end(self):
        stub.queue_responses([
            _llm_response("partial", "relevant", True),
            _llm_response("insufficient", "relevant", True),
        ])
        result = self._compute()
        self.assertEqual(result["decision"], "review")
        self.assertTrue(result["review_required"])
        self.assertEqual(self.contract.get_evaluation("MS-001"), result)

    def test_get_evaluation_unknown_id(self):
        self.assertIsNone(self.contract.get_evaluation("NOPE"))

    def test_empty_milestone_id_rejected(self):
        with self.assertRaises(stub.vm.UserError):
            self.contract.compute("", CLAIM, EVIDENCE, QUOTE)

    def test_oversized_evidence_rejected(self):
        with self.assertRaises(stub.vm.UserError):
            self.contract.compute("MS-002", CLAIM, "x" * 50001, QUOTE)

    def test_fabricated_quote_flagged(self):
        stub.queue_responses([
            _llm_response("supported", "relevant", True),
            _llm_response("supported", "relevant", True),
        ])
        result = self.contract.compute(
            "MS-003", CLAIM, EVIDENCE, "5,000 monthly active users"
        )
        self.assertFalse(result["key_figure_present"])


if __name__ == "__main__":
    unittest.main()
