import os
import asyncio
import argparse
from web3 import Web3
from dotenv import load_dotenv
from cast import calldata_decoder
from colorama import Fore
from simulation import simulate

load_dotenv()

class TransactionProcessor:
    @staticmethod
    def extract_address_from_add_liquidity(bytes_data):
        output = calldata_decoder(bytes_data)
        address = output['matches'][0]['argument1']
        return Web3.to_checksum_address(address)

    @staticmethod
    def process_transaction(web3, tx_hash, owner_address):
        try:
            tx = web3.eth.get_transaction(tx_hash)
            input_data = web3.to_hex(tx['input'])
            
            if input_data[:10] == "0xf305d719" and tx['from'] == owner_address:
                print(f"{Fore.GREEN}The owner has added liquidity to the pair{Fore.RESET}")
                print(f"Hash: {web3.to_hex(tx['hash'])}")
                token = TransactionProcessor.extract_address_from_add_liquidity(input_data)
                return token
            elif input_data[:10] != "0x":
                print(f"{Fore.RED}{tx_hash}{Fore.RESET}")
                print(calldata_decoder(input_data))
            
            return None
        except Exception as e:
            print(f"Error handling the hash {tx_hash}: {e}")
            return None

class EventHandler:
    @staticmethod
    async def handle_transaction_event(web3, event, owner_address):
        tx_hash = web3.to_hex(event)
        token = TransactionProcessor.process_transaction(web3, tx_hash, owner_address)
        if token:
            return token
        return None

    @staticmethod
    async def handle_block_event(web3, event):
        block_number = web3.to_hex(event)
        print(f"{Fore.BLUE}New block mined: {block_number}{Fore.RESET}")
        # Add any block-specific processing here

class EventSniper:
    def __init__(self, web3_instance, owner_address):
        self.web3 = web3_instance
        self.owner_address = owner_address
        self.tx_filter = self.web3.eth.filter('pending')
        self.block_filter = self.web3.eth.filter('latest')

    async def snipe_events(self, poll_interval):
        while True:
            tx_events = self.tx_filter.get_new_entries()
            block_events = self.block_filter.get_new_entries()
            
            if tx_events:
                tx_results = await asyncio.gather(*[EventHandler.handle_transaction_event(self.web3, event, self.owner_address) for event in tx_events])
                token_address = next((result for result in tx_results if result is not None), None)
                if token_address:
                    return token_address
            
            if block_events:
                await asyncio.gather(*[EventHandler.handle_block_event(self.web3, event) for event in block_events])
            
            await asyncio.sleep(poll_interval)

async def main(owner_address, rpc_url):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    sniper = EventSniper(web3, owner_address)
    token_address = await sniper.snipe_events(0.1)
    print(f"Token address found: {token_address}")
    
    # Perform simulation - You can also buy the token here
    safe_block = simulate(token_address)
    print(f"Safe block found: {safe_block}")
    
    # Add any additional processing or actions with the safe_block here

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Snipe events for a specific owner address")
    parser.add_argument("owner_address", help="The owner address to monitor")
    parser.add_argument("--rpc-url", required=True, help="The RPC URL to connect to")
    args = parser.parse_args()
    
    asyncio.run(main(args.owner_address, args.rpc_url))