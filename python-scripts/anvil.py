import subprocess
import time
from web3 import Web3
from web3.exceptions import TransactionNotFound
from dotenv import load_dotenv
import os
from tools import extract_abi
import subprocess
import threading
import queue
from colorama import Fore
# Load environment variables
load_dotenv()

class AnvilInteractions:
    ANVIL_URL = "http://localhost:8545"
    ANVIL_EXECUTABLE = "anvil"
    UNISWAP_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Uniswap V2 Router
    WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'  # WETH address

    def __init__(self, RPC_URL ,additional_anvil_args=None):
        self.RPC_URL = RPC_URL
        self.additional_anvil_args = additional_anvil_args if additional_anvil_args else []
        self.anvil_process = None
        self.web3 = None
        self.uniswap = None
        self.start_anvil()
        self.setup_web3()
        self.WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'  # WETH address on Ethereum
        self.UNISWAP_ROUTER_ADDRESS = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  # Uniswap V2 Router

    def start_anvil(self):
        command = [self.ANVIL_EXECUTABLE, '--fork-url', self.RPC_URL] + self.additional_anvil_args

        def read_output(process, queue):
            for line in iter(process.stdout.readline, b''):
                queue.put(line)
            process.stdout.close()

        self.anvil_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        print("Starting Anvil...")
        
        output_queue = queue.Queue()
        thread = threading.Thread(target=read_output, args=(self.anvil_process, output_queue))
        thread.daemon = True
        thread.start()

        start_time = time.time()
        timeout = 60  # Adjust this value as needed

        while True:
            try:
                line = output_queue.get(timeout=0.1)
                print(line.strip())
                
                if "Listening on" in line or "Server started" in line:
                    print(f"{Fore.BLUE}Anvil started successfully {Fore.RESET}")
                    return True
                
                if "Error" in line or "Failed" in line:
                    print(f"{Fore.RED}Anvil startup error: {line}{Fore.RESET}")
                    return False

            except queue.Empty:
                if time.time() - start_time > timeout:
                    print(f"Anvil startup timed out after {timeout} seconds")
                    self.anvil_process.terminate()
                    return False

            if self.anvil_process.poll() is not None:
                print("Anvil process ended unexpectedly")
                return False

        return False
        
    def setup_web3(self):
        self.web3 = Web3(Web3.HTTPProvider(self.ANVIL_URL))
        if not self.web3.is_connected():
            raise Exception("Failed to connect to Anvil")
        print("Connected to Anvil")
        
        uniswap_abi = extract_abi(self.UNISWAP_ADDRESS)
        self.uniswap = self.web3.eth.contract(address=self.UNISWAP_ADDRESS, abi=uniswap_abi)
    def impersonate_account(self, address):
        try:
            response = self.web3.provider.make_request("anvil_impersonateAccount", [address])
            print(f"Impersonation response for {address}: {response}")
            return True
        except Exception as e:
            print(f"Error impersonating account {address}: {e}")
            return False

    def stop_impersonating(self, address):
        try:
            self.web3.provider.make_request("anvil_stopImpersonatingAccount", [address])
            print(f"Stopped impersonating {address}")
            return True
        except Exception as e:
            print(f"Error stopping impersonation of {address}: {e}")
            return False
    def execute_contract_function(self, contract, function_name, *args, **kwargs):
        try:
            function = getattr(contract.functions, function_name)
            transaction = function(*args).build_transaction(kwargs)
            
            # Remove 'data' from kwargs if it exists
            transaction.pop('data', None)
            
            # Send the transaction using eth_sendTransaction RPC method
            tx_hash = self.web3.eth.send_transaction(transaction)
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction successful. Hash: {tx_hash.hex()}")
            return tx_receipt
        except Exception as e:
            print(f"Error executing contract function {function_name}: {e}")
            return None
    def get_token_balance(self, token_address, account_address):
        balanceOf_abi = [
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "owner",
                        "type": "address"
                    }
                ],
                "name": "balanceOf",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        token_contract = self.web3.eth.contract(address=token_address, abi=balanceOf_abi)
        balance = token_contract.functions.balanceOf(account_address).call()
        return self.web3.from_wei(balance, 'ether')
    
    #It's not yet working for some reason
    def send_buy_transaction(self, token_address, amount_eth, sender_address):
        nonce = self.web3.eth.get_transaction_count(sender_address)
        
        uniswap_txn = self.uniswap.functions.swapExactETHForTokens(
            0,  # Set to 0, or specify minimum amount of tokens you want to receive
            [self.WETH_ADDRESS, token_address],
            sender_address,
            int(time.time()) + 600  # 10 minutes deadline
        ).build_transaction({
            'from': sender_address,
            'value': self.web3.to_wei(amount_eth, 'ether'),
            'gas': 250000,  # Adjust as needed
            'gasPrice': self.web3.to_wei('20', 'gwei'),  # Adjust as needed
            'nonce': nonce,
        })
        
        tx_hash = self.web3.eth.send_transaction(uniswap_txn)
        print(f"Buy transaction sent. Hash: {tx_hash.hex()}")
        return tx_hash

    def sell_token(self, token_address, amount_tokens, sender_address):
        nonce = self.web3.eth.get_transaction_count(sender_address)
        
        # First, approve the Uniswap Router to spend tokens
        token_contract = self.web3.eth.contract(address=token_address, abi=extract_abi(token_address))
        approve_txn = token_contract.functions.approve(
            self.UNISWAP_ROUTER_ADDRESS,
            self.web3.to_wei(amount_tokens, 'ether')  # Assumes 18 decimals, adjust if needed
        ).build_transaction({
            'from': sender_address,
            'gas': 100000,  # Adjust as needed
            'gasPrice': self.web3.to_wei('20', 'gwei'),  # Adjust as needed
            'nonce': nonce,
        })
        
        # Send approval transaction
        approve_tx_hash = self.web3.eth.send_transaction(approve_txn)
        self.web3.eth.wait_for_transaction_receipt(approve_tx_hash)
        print(f"Approval transaction was successful. Hash: {approve_tx_hash.hex()}")
        
        # Now, sell the tokens
        nonce += 1
        sell_txn = self.uniswap.functions.swapExactTokensForETH(
            self.web3.to_wei(amount_tokens, 'ether'),  # Assumes 18 decimals, adjust if needed
            0,  # Set to 0, or specify minimum amount of ETH you want to receive
            [token_address, self.WETH_ADDRESS],
            sender_address,
            int(time.time()) + 600  # 10 minutes deadline
        ).build_transaction({
            'from': sender_address,
            'gas': 250000,  # Adjust as needed
            'gasPrice': self.web3.to_wei('20', 'gwei'),  # Adjust as needed
            'nonce': nonce,
        })
        
        # Send sell transaction
        sell_tx_hash = self.web3.eth.send_transaction(sell_txn)
        
        print(f"Sell transaction sent. Hash: {sell_tx_hash.hex()}")
        
        # Wait for the transaction to be mined
        sell_tx_receipt = self.web3.eth.wait_for_transaction_receipt(sell_tx_hash)
        print(f"Sell transaction was successful. Block: {sell_tx_receipt['blockNumber']}")
        
        return sell_tx_receipt

    def cleanup(self):
        if self.anvil_process:
            self.anvil_process.terminate()
            self.anvil_process.wait()
            print("Anvil process terminated")

# Usage example:
def main():
    RPC_URL = os.getenv('RPC_URL')
    anvil_args = [
        #'--no-mining',
        #'--order', 'fifo'#  ,
        #'--fork-block-number', '13000000',  
        # '--block-time', '10',  # Example: Produces a new block every 10 seconds
        # '--accounts', '15',    # Example: Set the number of accounts to 15
        # '--balance', '300'     # Example: Set the balance of accounts to 300 ETH
    ]
    anvil = AnvilInteractions(RPC_URL , additional_anvil_args=anvil_args)
    impersonated_address = '0xF8f96B83f85167CD7D3bdF9A6591fC37e53Cb75E'
    token_address = '0x6B175474E89094C44Da98b954EedeAC495271d0F'  # DAI for example

    try:
        if anvil.impersonate_account(impersonated_address):
            initial_balance = anvil.get_token_balance(token_address, impersonated_address)
            print(f"Initial balance: {initial_balance} tokens")

            hash =anvil.send_buy_transaction(token_address, 0.1, impersonated_address)
            print(f"Buy transaction hash: {hash.hex()}")
            
            mid_balance = anvil.get_token_balance(token_address, impersonated_address)
            print(f"Balance after buying: {mid_balance} tokens")

            anvil.sell_token(token_address, mid_balance - initial_balance, impersonated_address)
            
            final_balance = anvil.get_token_balance(token_address, impersonated_address)
            print(f"Final balance: {final_balance} tokens")

            anvil.stop_impersonating(impersonated_address)
    finally:
        anvil.cleanup()

if __name__ == "__main__":
    main()