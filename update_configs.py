import json
import re
import os

# Paths to the files we need to update
CONTRACT_JSON = r'c:\Users\acer\Desktop\new final year project\CertificateVerification\build\contracts\CertificateVerification.json'
MAIN_PY = r'c:\Users\acer\Desktop\new final year project\CertificateVerification\Main.py'
JAVA_PROPS = r'c:\Users\acer\Desktop\new final year project\AnalyticsService\src\main\resources\application.properties'
TRIGGER_PY = r'c:\Users\acer\Desktop\new final year project\trigger_event.py'
INSPECT_PY = r'c:\Users\acer\Desktop\new final year project\inspect_logs.py'

def update_configs():
    # 1. Extraction: Get the latest address from Truffle build
    try:
        with open(CONTRACT_JSON, 'r') as f:
            data = json.load(f)
            # Find the address in the networks section
            network_id = list(data['networks'].keys())[-1] # Usually '5777' for Ganache
            new_address = data['networks'][network_id]['address']
            print(f"[SUCCESS] Found new contract address: {new_address}")
    except Exception as e:
        print(f"[ERROR] Could not read Truffle build file: {e}")
        return

    # 2. Update Main.py (Python Backend)
    try:
        with open(MAIN_PY, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regex to find deployed_contract_address = '0x...'
        pattern = r"deployed_contract_address = '0x[a-fA-F0-9]{40}'"
        replacement = f"deployed_contract_address = '{new_address}'"
        
        new_content, count = re.subn(pattern, replacement, content)
        with open(MAIN_PY, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[SUCCESS] Updated Main.py ({count} occurrences)")
    except Exception as e:
        print(f"[ERROR] Could not update Main.py: {e}")

    # 3. Update application.properties (Java Backend)
    try:
        with open(JAVA_PROPS, 'r') as f:
            lines = f.readlines()
        
        with open(JAVA_PROPS, 'w') as f:
            for line in lines:
                if line.startswith('blockchain.contract.address='):
                    f.write(f'blockchain.contract.address={new_address}\n')
                else:
                    f.write(line)
        print(f"[SUCCESS] Updated application.properties")
    except Exception as e:
        print(f"[ERROR] Could not update application.properties: {e}")



if __name__ == "__main__":
    update_configs()
