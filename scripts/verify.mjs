// Read an evaluation back from a deployed verifier contract (Studio Next).
// Usage: node verify.mjs <contractAddress> <evaluationId>
import { createClient } from 'genlayer-js';
import { studioDevnet } from 'genlayer-js/chains';
import { http } from 'viem';

const [,, addr, id] = process.argv;
if (!addr || !id) {
  console.error('usage: node verify.mjs <contractAddress> <evaluationId>');
  process.exit(1);
}
const client = createClient({ chain: studioDevnet, transport: http(studioDevnet.rpcUrls.default.http[0]) });
const result = await client.readContract({ address: addr, functionName: 'get_evaluation', args: [id] });
console.log(`get_evaluation(${id}) =>`, JSON.stringify(result, null, 2));
