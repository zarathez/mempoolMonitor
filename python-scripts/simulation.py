import time
from web3 import Web3
from dotenv import load_dotenv
import os
from tools import extract_abi
from anvil import AnvilInteractions

def simulate(token):

    anvil_args = [
        #'--fork-block-number', str(entryblock),
        '--no-mining',
        #'--accounts <ACCOUNTS>', 'Set the number of accounts. [default: 10]',
        #'--auto-impersonate', 'Enable autoImpersonate on startup.',
        #'--balance <BALANCE>', 'Set the balance of the accounts. [default: 10000]',
        #'--derivation-path <DERIVATION_PATH>', 'Set the derivation path of the child key to be derived. [default: m/44’/60’/0’/0/]',
        #'-h, --help', 'Print help information.',
        #'--hardfork <HARDFORK>', 'Choose the EVM hardfork to use e.g. shanghai, paris, london, etc… [default: latest]',
        #'--init <PATH>', 'Initialize the genesis block with the given genesis.json file.',
        #'-m, --mnemonic <MNEMONIC>', 'BIP39 mnemonic phrase used for generating accounts.',
        '-p' , '7545' #--port <PORT>', 'Port number to listen on. [default: 8545]',
        #'--steps-tracing', 'Enable steps tracing used for debug calls returning geth-style traces. [aliases: tracing]',
        #'--ipc [<PATH>]', 'Starts an IPC endpoint at the given PATH argument or the default path: unix: tmp/anvil.ipc, windows: \\.\pipe\anvil.ipc.',
        #'--silent', 'Don’t print anything on startup.',
        #'--timestamp <TIMESTAMP>', 'Set the timestamp of the genesis block.',
        #'-V, --version', 'Print version information.',
        #'--disable-default-create2-deployer', 'Disables deploying the default CREATE2 factory when running Anvil without forking.',
        #'--fork-url <URL>', 'Fetch state over a remote endpoint instead of starting from an empty state.',
        #'--fork-retry-backoff <BACKOFF>', 'Initial retry backoff on encountering errors.',
        #'--retries <retries>', 'Number of retry requests for spurious networks (timed out requests). [default: 5]',
        #'--timeout <timeout>', 'Timeout in ms for requests sent to remote JSON-RPC server in forking mode. [default: 45000]',
        #'--compute-units-per-second <CUPS>', 'Sets the number of assumed available compute units per second for this provider. [default: 330]      See also, Alchemy Ratelimits.',
        #'--no-rate-limit', 'Disables rate limiting for this node’s provider. Will always override --compute-units-per-second if present. [default: false]      See also, Alchemy Ratelimits.',
        #'--no-storage-caching', 'Disables RPC caching; all storage slots are read from the endpoint. This flag overrides the project’s configuration file (Must pass –fork-url in the same command-line).',
        #'--base-fee <FEE>', 'The base fee in a block.',
        #'--block-base-fee-per-gas <FEE>', 'The base fee in a block.',
        #'--chain-id <CHAIN_ID>', 'The chain ID. [default: 31337]',
        #'--code-size-limit <CODE_SIZE>', 'EIP-170: Contract code size limit in bytes. Useful to increase for tests. [default: 0x6000 (~25kb)]',
        #'--gas-limit <GAS_LIMIT>', 'The block gas limit.',
        #'--gas-price <GAS_PRICE>', 'The gas price.',
        #'--allow-origin <allow-origin>', 'Set the CORS allow_origin. [default: *]',
        #'--no-cors', 'Disable CORS.',
        #'--host <HOST>', 'The IP address the server will listen on.',
        #'--config-out <OUT_FILE>', 'Writes output of anvil as json to user-specified file.',
        #'--prune-history', 'Don’t keep full chain history.'
        #'--no-mining'
        #'--order', 'fifo'
        #'--block-time', '3'
    ]
    
    anvil = AnvilInteractions('http://127.0.0.1:8545', additional_anvil_args=anvil_args)
    
    impersonated_address = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
    token = anvil.web3.to_checksum_address(token)  
    impersonated_address = anvil.web3.to_checksum_address(impersonated_address)
    
    try:
        if not anvil.impersonate_account(impersonated_address):
            raise Exception("Failed to impersonate account")

        current_block = anvil.web3.eth.block_number
        max_attempts = 10  # Limit the number of attempts

        print(f"Starting the tests at block {current_block}")
        for attempt in range(max_attempts):
            initial_balance = anvil.get_token_balance(token, impersonated_address)
            
            
            try:
                tx_hash = anvil.send_buy_transaction(token, 0.1, impersonated_address)
                

                
                # Mine a block
                anvil.web3.provider.make_request("evm_mine", [])
                current_block += 1
                print(f"Mined block {current_block}")


                # Check balance after mining
                new_balance = anvil.get_token_balance(token, impersonated_address)
                
                if new_balance > initial_balance:
                    print(f"Token purchase successful. Balance increased from {initial_balance} to {new_balance}")
                    return current_block
                else:
                    print(f"Balance didn't increase. Initial: {initial_balance}, New: {new_balance}")
                    print("Trying in next block")

            except Exception as e:
                print(f"Error during buy attempt: {e}")

            # Mine an additional block to ensure any pending transactions are processed
            anvil.web3.provider.make_request("evm_mine", [])
            current_block += 1
            print(f"Mined additional block {current_block}")

        print(f"Failed to purchase token after {max_attempts} attempts")
        return None

    finally:
        anvil.stop_impersonating(impersonated_address)
        anvil.cleanup()

def main():
    load_dotenv()
    token_address = '0x6B175474E89094C44Da98b954EedeAC495271d0F'  # DAI token address
    whitelisted_block = simulate(token_address)
    if whitelisted_block:
        print(f"First whitelisted block: {whitelisted_block}")
    else:
        print("Failed to find a whitelisted block")

if __name__ == "__main__":
    main()