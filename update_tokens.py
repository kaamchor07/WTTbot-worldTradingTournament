"""
Quick script to update API tokens
Run this before the competition starts with fresh tokens from browser DevTools
"""

def update_tokens():
    print("""
╔══════════════════════════════════════════════════════════════╗
║              TOKEN UPDATE HELPER                             ║
╚══════════════════════════════════════════════════════════════╝

How to get fresh tokens:
1. Open https://wttplay.worldtradingtournament.com/
2. Open DevTools (F12) -> Network tab
3. Make any trade or refresh a chart
4. Find a request to 'tradequote' or similar
5. Look in Request Headers for:
   - Authorization: Bearer XXXXXXXX
   - tradetoken: eyJhbGci...

""")
    
    print("Current tokens in config.py:")
    print("-" * 60)
    
    # Read current config
    with open('config.py', 'r') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "'Authorization':" in line:
            print(f"Line {i+1}: {line.strip()}")
        if "'tradetoken':" in line:
            print(f"Line {i+1}: {line.strip()}")
    
    print("-" * 60)
    print("\nDo you want to update the tokens? (y/n): ", end='')
    
    response = input().strip().lower()
    
    if response != 'y':
        print("❌ Cancelled")
        return
    
    print("\nEnter new Authorization Bearer token (just the token part, no 'Bearer '): ")
    auth_token = input().strip()
    
    print("\nEnter new tradetoken (the full JWT starting with eyJ...): ")
    trade_token = input().strip()
    
    # Update config file
    new_lines = []
    for line in lines:
        if "'Authorization':" in line:
            new_lines.append(f"    'Authorization': 'Bearer {auth_token}',\n")
        elif "'tradetoken':" in line:
            new_lines.append(f"    'tradetoken': '{trade_token}',\n")
        else:
            new_lines.append(line)
    
    # Write updated config
    with open('config.py', 'w') as f:
        f.writelines(new_lines)
    
    print("\n✓ Tokens updated in config.py!")
    print("\nTesting connection...")
    
    # Test the connection
    import subprocess
    result = subprocess.run(['python3', 'test_api.py'], capture_output=True, text=True)
    
    if 'success' in result.stdout.lower() and 'BadRequest' not in result.stdout:
        print("\n✅ SUCCESS! API connection is working!")
    else:
        print("\n⚠️  API test returned an error. Check the output above.")
        print("\nLast 500 chars of output:")
        print(result.stdout[-500:])


if __name__ == "__main__":
    update_tokens()
