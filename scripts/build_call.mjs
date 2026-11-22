// Build an addTransaction payload that CALLS a method on a deployed
// intelligent contract (Studio Next, chain 61997).
// Usage: node build_call.mjs <senderAddress> <contractAddress> <functionName> <jsonArgsArray>
// Prints a ---TX--- JSON block: {to, data, value, ...} for sign_broadcast.py.
import { createClient, abi } from 'genlayer-js';
import { studioDevnet } from 'genlayer-js/chains';
import { http, encodeFunctionData } from 'viem';

const CONSENSUS = studioDevnet.consensusMainContract.address;
const [,, sender, address, functionName, argsJson] = process.argv;
if (!sender || !address || !functionName || argsJson === undefined) {
  console.error('usage: node build_call.mjs <sender> <contract> <function> <jsonArgs>');
  process.exit(1);
}
const callArgs = JSON.parse(argsJson);
const client = createClient({ chain: studioDevnet, transport: http(studioDevnet.rpcUrls.default.http[0]) });

async function main() {
  const fees = await client.estimateTransactionFees({});
  const calldataObj = abi.calldata.makeCalldataObject(functionName, callArgs, undefined);
  const methodCalldata = abi.calldata.encode(calldataObj);
  const serializedData = abi.transactions.serialize([methodCalldata, false]);
  const validUntil = BigInt(Math.floor(Date.now() / 1000) + 3600);
  const params = {
    sender,
    recipient: address,
    numOfInitialValidators: BigInt(studioDevnet.defaultNumberOfInitialValidators),
    maxRotations: BigInt(studioDevnet.defaultConsensusMaxRotations),
    validUntil,
    saltNonce: 0n,
    userValue: 0n,
    feesDistribution: fees.distribution,
    txCalldata: serializedData,
    messageAllocations: fees.messageAllocations ?? [],
  };
  const data = encodeFunctionData({
    abi: studioDevnet.consensusMainContract.abi,
    functionName: 'addTransaction',
    args: [params],
  });
  const value = fees.feeValue;
  console.log('---TX---');
  console.log(JSON.stringify({ to: CONSENSUS, data, value: value.toString(), valueGen: (Number(value) / 1e18).toFixed(6), validUntil: validUntil.toString(), fn: functionName, args: callArgs }));
}
main().catch(e => { console.error('BUILD FAIL:', e.message); process.exit(1); });
