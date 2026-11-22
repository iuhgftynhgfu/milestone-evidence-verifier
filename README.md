# Milestone Evidence Verifier — GenLayer Intelligent Contract

An Intelligent Contract that judges whether a project's **claimed milestone
is supported by the evidence submitted for it** — metrics, analytics
excerpts, links, or screenshot descriptions. Example: a team claims "1,000
active users" for a milestone; the evidence is an analytics summary. This
contract decides whether the evidence backs the claim, so milestone payouts
and progress reviews can be checked by consensus instead of by trust.

## Live deployment (GenLayer Studio Next, chain 61997)

- **Contract:** `0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f`
- **Deploy TX:** `0x40bd08259cf307730f7bc08e3589d87a4c4b865f07cf737d916dd81fc15a9cf6`
- **Explorer (contract):** https://explorer-studio-dev.genlayer.com/address/0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f
- **Explorer (deploy tx):** https://explorer-studio-dev.genlayer.com/tx/0x40bd08259cf307730f7bc08e3589d87a4c4b865f07cf737d916dd81fc15a9cf6
- **RPC:** https://studio-next.genlayer.com/api
- **Deployer:** `0x898bc9eE1DD84Ab7E2319faAeC6cEDa864Ed2F00` (fresh testnet keypair, Studio faucet)
- **py-genlayer version (Depends):** `1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` (supports TreeMap + `from genlayer import *`)

Full on-chain proof (both decision paths, read back from the chain) is in
[ONCHAIN_PROOF.md](ONCHAIN_PROOF.md). Ready-to-paste portal text is in
[SUBMISSION.md](SUBMISSION.md).

## What it judges

`compute(milestone_id, claim, evidence, candidate_quote)`:

| Input | Meaning |
|---|---|
| `milestone_id` | Caller-chosen id the evaluation is stored under |
| `claim` | The milestone claim, e.g. "1,000 active users in the first month" |
| `evidence` | Submitted evidence text (metrics, analytics excerpts, links) |
| `candidate_quote` | A key figure/quote the submitter says is in the evidence |

The LLM assesses the evidence and returns three fields; the contract
derives the decision deterministically:

| Assessment | Decision |
|---|---|
| `supported` + `relevant` + metric found | `accept` |
| `contradicted`, or `irrelevant` | `reject` |
| anything else (`partial`, `insufficient`, `ambiguous`, …) | `review` |

`get_evaluation(milestone_id)` reads the stored result back.

A deterministic literal-substring check (`key_figure_present`) records
whether the candidate quote actually appears in the evidence — computed
outside the LLM prompt, so a fabricated quote is flagged even if the LLM
is fooled.

## Why validators can't be fooled by a dishonest leader

The validator does **independent re-evaluation**, not a structure check.
Every validator issues its OWN `exec_prompt` call with the SAME assessment
prompt the leader used, derives its own decision from its own assessment
via the shared deterministic table, and accepts the leader's result only
when the bound (assessment, decision) pair agrees with its own:

- A leader claiming `supported -> accept` and a leader claiming
  `contradicted -> reject` for the same milestone cannot both pass.
- Labels inside the review class (`partial` / `insufficient` / `ambiguous`)
  all mean "the evidence does not establish the claim, a human must
  review", so two honest validators may use different review-class labels
  and still agree — wording variance must not stall consensus.
- Any malformed output from the validator's own LLM call votes `False`
  (disagree rather than agree on broken output).

All nondeterministic calls live inside
`gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`; contract storage is
never accessed inside those blocks.

## Tests (30 passing, stdlib-only, no network)

The `genlayer` module is stubbed (`tests/genlayer_stub.py`) with scripted
LLM responses, so every scenario is deterministic:

```bash
python -m unittest -v tests.test_milestone_validator
# Ran 30 tests — OK
```

Coverage: opposite assessments must not both pass (both directions);
agreement passes (accept and reject); review-class equivalence; broken
validator output disagrees (malformed JSON, missing fields, invalid enum);
structural checks retained (decision-table inconsistency,
`key_figure_present` mismatch, non-Return leader result, cross-field
inconsistency); decision-table rows; end-to-end `compute()` runs
(agreement stores, disagreement stores nothing, leader/validator prompts
byte-identical, fabricated quote flagged, oversized evidence rejected).

## Reproduce the deployment

```bash
cd scripts
npm install            # genlayer-js + viem (builds the addTransaction calldata)
# Deploy (needs DEPLOYER_KEYFILE pointing at a JSON {"address","key"} file,
# or place .deployer-key.json at the repo parent):
node build_deploy.mjs ../contracts/milestone_contract.py <SENDER> | awk '/---TX---/{f=1;next} f' > /tmp/tx.json
python3 sign_broadcast.py /tmp/tx.json
# Call compute:
node build_call.mjs <SENDER> <CONTRACT> compute '["MS-001","<claim>","<evidence>","<quote>"]' | awk '/---TX---/{f=1;next} f' > /tmp/tx.json
python3 sign_broadcast.py /tmp/tx.json
# Read back:
node verify.mjs <CONTRACT> MS-001
```

Documented gotchas (all handled by these scripts): the GenLayer node
rejects 2-param `eth_estimateGas` (use 1-param); gas price 0, legacy tx
with no `type` field; transactions go to the consensus contract
(`0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575`) via `addTransaction`, not
directly to the contract. The `genlayer` PyPI package is an empty
placeholder — there is no `genlayer` CLI to rely on.

## Layout

```
contracts/milestone_contract.py   the intelligent contract
tests/                            stub-based local tests (30 passing)
scripts/                          deploy / call / sign+broadcast / verify
ONCHAIN_PROOF.md                  live tx hashes + read-back results
SUBMISSION.md                     ready-to-paste portal submission text
```
