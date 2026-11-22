"""Sign + broadcast a GenLayer tx with the fresh deployer keypair.

Reads a TX JSON file ({"to","data","value"}), signs with the key in
../.deployer-key.json (mode 600, generated for this campaign — never the
user's wallet), and broadcasts to Studio Next (chain 61997).

GenLayer node quirks (proven by the je26 Pay & Prove deploy):
- eth_estimateGas accepts ONLY 1 param — use w3.manager.request_blocking.
- gasPrice 0, legacy tx WITHOUT a "type" field.

Usage: python3 sign_broadcast.py <txfile> [outfile]
"""
import json
import os
import sys

from eth_account import Account
from web3 import Web3

TXFILE = sys.argv[1]
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/genlayer_broadcast_result.json"
KEYFILE = os.environ.get("DEPLOYER_KEYFILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".deployer-key.json"))
RPC = "https://studio-next.genlayer.com/api"
CHAIN_ID = 61997

txj = json.load(open(TXFILE))
keydata = json.load(open(KEYFILE))
acct = Account.from_key(keydata["key"])
sender = acct.address
print("sender:", sender)

w3 = Web3(Web3.HTTPProvider(RPC))
print("balance GEN:", w3.eth.get_balance(sender) / 1e18)
nonce = w3.eth.get_transaction_count(sender, "latest")
print("nonce:", nonce)

txobj = {"to": txj["to"], "from": sender, "data": txj["data"], "value": int(txj["value"])}
est = w3.manager.request_blocking("eth_estimateGas", [txobj])
est = int(est, 16) if isinstance(est, str) else int(est)
print("gas estimate:", est)
gas = int(est * 1.2)
print("gas limit (x1.2):", gas)

tx = {
    "to": txj["to"],
    "data": txj["data"],
    "value": int(txj["value"]),
    "gas": gas,
    "gasPrice": 0,
    "nonce": nonce,
    "chainId": CHAIN_ID,
}
signed = acct.sign_transaction(tx)
txhash = w3.eth.send_raw_transaction(signed.raw_transaction)
print("TX HASH:", txhash.hex())
json.dump(
    {"txHash": txhash.hex(), "nonce": nonce, "gas": gas, "sender": sender},
    open(OUTFILE, "w"),
    indent=2,
)
print("wrote", OUTFILE)
