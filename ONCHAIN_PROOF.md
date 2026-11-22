# Milestone Evidence Verifier — on-chain proof (Studio Next, chain 61997)

## Contract

- **MilestoneEvidenceVerifier:** `0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f`
- **Deploy TX:** `0x40bd08259cf307730f7bc08e3589d87a4c4b865f07cf737d916dd81fc15a9cf6` (FINALIZED, FINISHED_WITH_RETURN)
- **Explorer (contract):** https://explorer-studio-dev.genlayer.com/address/0xC30B7e1c733a836B5c520360DDcdBD88Fc99144f
- **Explorer (deploy tx):** https://explorer-studio-dev.genlayer.com/tx/0x40bd08259cf307730f7bc08e3589d87a4c4b865f07cf737d916dd81fc15a9cf6
- **Consensus contract:** `0xb7278A61aa25c888815aFC32Ad3cC52fF24fE575`
- **RPC:** https://studio-next.genlayer.com/api
- **Deployer:** `0x898bc9eE1DD84Ab7E2319faAeC6cEDa864Ed2F00` (fresh testnet keypair, funded from the Studio faucet)
- **py-genlayer version (Depends):** `1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- **Contract code verified on-chain** via `gen_getContractCode` (18,984 bytes, starts with the pinned Depends header).

## Verified evaluations (both decision paths, read back via genlayer-js readContract)

### MS-001 — supported claim → ACCEPT

- Claim: "Milestone: 1,000 active users in the first month"
- Evidence: "Analytics dashboard export: 1,024 monthly active users, 31 days after launch."
- Candidate quote: "1,024 monthly active users"
- **compute TX:** `0x534762f1ef3348d78bc2404f38e73d995c0c7bb53d263ba7c65a64bb380cac55` (FINALIZED, FINISHED_WITH_RETURN)
- Explorer: https://explorer-studio-dev.genlayer.com/tx/0x534762f1ef3348d78bc2404f38e73d995c0c7bb53d263ba7c65a64bb380cac55
- Stored result (`get_evaluation("MS-001")`):
  - `claim_support: supported`, `metric_relevance: relevant`, `metric_found: true`
  - `decision: accept`, `key_figure_present: true`
  - `evaluation_complete: true`, `review_required: false`
  - Explanation: "The analytics dashboard export shows 1,024 monthly active users 31 days after launch, which directly supports the milestone claim of 1,000 active users in the first month."

### MS-002 — contradicted claim → REJECT

- Claim: "Milestone: 10,000 active users in the first month"
- Evidence: "Analytics dashboard export: 1,024 monthly active users, 31 days after launch."
- Candidate quote: "10,000 monthly active users"
- **compute TX:** `0xc060e0341afa0d2d339f05eba98fd08f151b33e1bbd8637c88679d3369637e69` (FINALIZED, FINISHED_WITH_RETURN)
- Explorer: https://explorer-studio-dev.genlayer.com/tx/0xc060e0341afa0d2d339f05eba98fd08f151b33e1bbd8637c88679d3369637e69
- Stored result (`get_evaluation("MS-002")`):
  - `claim_support: contradicted`, `metric_relevance: relevant`, `metric_found: true`
  - `decision: reject`, `key_figure_present: false` (the fabricated figure is not in the evidence)
  - `evaluation_complete: true`, `review_required: false`
  - Explanation: "The milestone claims 10,000 active users, but the submitted analytics dashboard export shows only 1,024 monthly active users, which contradicts the claim."

## How the judging works

`compute()` runs the assessment inside `gl.vm.run_nondet_unsafe`: the
leader proposes an assessment (`claim_support`, `metric_relevance`,
`metric_found`) and the contract derives the decision from a deterministic
table. Every validator independently re-runs the SAME prompt, derives its
own decision, and accepts the leader only when the bound
(assessment, decision) pair agrees with its own — review-class labels
(partial / insufficient / ambiguous) count as agreeing with each other.
The agreed result is stored on-chain under the milestone id.

## Deploy method (proven)

- Build addTransaction calldata with the genlayer-js SDK in Node
  (`scripts/build_deploy.mjs` for deploys, `scripts/build_call.mjs` for
  method calls).
- Sign + broadcast with web3.py / eth_account
  (`scripts/sign_broadcast.py`): 1-param `eth_estimateGas`, gas = estimate
  × 1.2, gasPrice 0, legacy tx WITHOUT a `type` field, chainId 61997.
- The deployed address is read from the deploy transaction's
  `to_address` via `sim_getTransactionsForAddress`, and confirmed with
  `gen_getContractCode`.
