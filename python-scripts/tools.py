import requests
import os
from dotenv import load_dotenv

load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

def extract_text_between_brackets(input_string):
    start_index = input_string.find('[')
    end_index = input_string.rfind(']')

    if start_index == -1 or end_index == -1:
        return None

    return input_string[start_index:end_index + 1]

def extract_abi(address):
    url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_API_KEY}"
    r = requests.get(url)
    return r.json()['result']

def extract_source_code(address):
    url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={ETHERSCAN_API_KEY}"
    r = requests.get(url)
    result = r.json()['result'][0]['SourceCode']  # Extract the source code from the JSON response
    return format_source_code(result)

def format_source_code(source_code):
    import re
    # Remove extraneous newlines and spaces
    formatted_code = re.sub(r'\r\n|\r|\n', '\n', source_code.strip())
    return formatted_code

if __name__ == "__main__":
    address = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
    abi = extract_abi(address)
    print(abi)

    # source_code = extract_source_code(address)
    
    # with open('source_code.sol', 'w') as file:
    #     file.write(source_code)
    
    # print("Source code written to source_code.sol")

