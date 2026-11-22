# Portal submission text — Milestone Evidence Verifier (Intelligent Contract)

Copy the sections below into the GenLayer Builder portal
(Intelligent Contracts contribution). Replace `<REPO-URL>` with the public
GitHub URL of this repo once pushed.

## Title

Milestone Evidence Verifier — consensus judging of milestone claims against submitted evidence

## Description

An Intelligent Contract that judges whether a project's claimed milestone
is supported by the evidence submitted for it (metrics, analytics
excerpts, links). Example: a team claims "1,000 active users" for a
milestone; the contract checks the analytics evidence and returns a
consensus decision — accept, reject, or review — so milestone payouts and
progress reviews can be checked by consensus instead of by trust.

`compute(milestone_id, claim, evidence, candidate_quote)` assesses the
evidence with an LLM and derives the decision from a deterministic table:
supported + relevant + metric found → accept; contradicted or irrelevant →
reject; otherwise review. `get_evaluation(milestone_id)` reads the stored
result back. A deterministic substring check (`key_figure_present`)
records whether the submitter's key figure actually appears in the
evidence, so fabricated quotes are flagged outside the LLM prompt.

The validator model is independent re-evaluation, not a structure check:
every validator issues its OWN exec_prompt call with the SAME prompt the
leader used, derives its own decision from its own assessment, and accepts
the leader only when the bound (assessment, decision) pair agrees with its
own. Opposite assessments cannot both pass. Review-class labels (partial /
insufficient / ambiguous) count as agreeing with each other, so wording
variance between honest validators does not stall consensus. Malformed
validator output votes False.

## What it judges

Whether a milestone claim (e.g. "1,000 active users in the first month")
is supported, contradicted, or unestablished by the submitted evidence
(e.g. an analytics dashboard export).

## Evidence links

- Repository: <REPO-URL>
- Contract source: <REPO-URL>/blob/main/contracts/milestone_contract.py
- Live contract (Studio Next, chain 61997): 0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f
- Explorer (contract): https://explorer-studio-dev.genlayer.com/address/0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f
- Deploy TX: https://explorer-studio-dev.genlayer.com/tx/0x40bd08259cf307730f7bc08e3589d87a4c4b865f07cf737d916dd81fc15a9cf6
- Write TX 1 (MS-001, supported → accept): https://explorer-studio-dev.genlayer.com/tx/0x534762f1ef3348d78bc2404f38e73d995c0c7bb53d263ba7c65a64bb380cac55
- Write TX 2 (MS-002, contradicted → reject): https://explorer-studio-dev.genlayer.com/tx/0xc060e0341afa0d2d339f05eba98fd08f151b33e1bbd8637c88679d3369637e69
- On-chain proof doc: <REPO-URL>/blob/main/ONCHAIN_PROOF.md
- Tests: 30/30 passing locally (stdlib unittest, stubbed genlayer module) — `python -m unittest -v tests.test_milestone_validator`
