import time
import sys
from web3 import Web3

# ANSI escape codes for green text
GREEN = "\033[92m"
RESET = "\033[0m"  # Reset to default color

# Set the ZenChain RPC URL
rpc_url = "https://zenchain-testnet.api.onfinality.io/public"

# Load data from priv-data.txt
file_path = "/root/chain-data/chains/priv-data.txt"

try:
    with open(file_path, 'r') as file:
        data = file.readlines()
        MY_ADDRESS = data[0].split('=')[1].strip()
        PRIVATE_KEY = data[1].split('=')[1].strip()
        SESSION_KEYS = data[2].split('=')[1].strip()
except FileNotFoundError:
    print("Private data file not found!")
    sys.exit(1)
except IndexError:
    print("Failed to load MY_ADDRESS, PRIVATE_KEY, or SESSION_KEYS from priv-data.txt.")
    sys.exit(1)

if SESSION_KEYS.startswith("0x"):
    SESSION_KEYS = SESSION_KEYS[2:]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(rpc_url))



# Check if connected to the ZenChain network
if not w3.is_connected():
    print('Not connected to ZenChain')
    sys.exit(1)

if not w3.is_address(MY_ADDRESS):
    print(f"Invalid address: {MY_ADDRESS}")
else:
    try:
        balance = w3.eth.get_balance(MY_ADDRESS)
        balance_in_ether = w3.from_wei(balance, 'ether')
        print(f"{GREEN}Balance for {MY_ADDRESS}: {balance_in_ether} ZCX{RESET}")
    except Exception as e:
        print(f"Error getting balance: {e}")



# Load the NativeStaking contract
NATIVE_STAKING_ADDRESS = '0x0000000000000000000000000000000000000800'
NATIVE_STAKING_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "bonded",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
    "inputs": [],
    "name": "chill",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
    },
]



staking_contract = w3.eth.contract(address=NATIVE_STAKING_ADDRESS, abi=NATIVE_STAKING_ABI)

chain_id = 8408

def send_transaction(func):
    nonce = w3.eth.get_transaction_count(MY_ADDRESS)
    transaction = func.build_transaction({
        'chainId': chain_id,
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
        # Create the explorer link using the transaction hash
        explorer_link = f"https://zentrace.io/tx/0x{tx_hash.hex()}"
        print(f"{GREEN}Transaction sent explorer Link: {explorer_link}")

        print(f"{GREEN} Now Please wait 10 second...!")
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt['status'] == 1:
            print("Transaction successful!")
        else:
            print("Transaction failed with details:")
    except Exception as e:
        print(f"An error occurred: {e}")

    return tx_hash

  

def check_bonded(address):
    return staking_contract.functions.bonded(address).call()



def check_and_chill(address):
    # Check if the user is bonded
    is_bonded = staking_contract.functions.bonded(address).call()

    if is_bonded:
        try:
            # If the user is bonded, call the chill function
            chill_function = staking_contract.functions.chill()
            send_transaction(chill_function)
            print(f"{GREEN}Your node has been restarted, you are now in chill mode!{RESET}")
        
        except Exception as e:
            print(f"Error occurred while calling chill function: {str(e)}")
    else:
        # If the user is not bonded, inform them
        print(f"{RED}You cannot chill, you must first register as a nominator.{RESET}")
      
