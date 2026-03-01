"""
Test API connection and inspect response structure
"""
import requests
import json

# API Configuration
API_BASE_URL = "https://wikitrade.interface002.com:32377/forexpayweb-v1/invoke-v3/tradequote"

API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer H4fj3iMsAYY8PDF8BPt4hOqvqQEC3qQC',
    'tradetoken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk0MDMzMTcsImlhdCI6MTc2OTMxNjkxNywidXNlcklkIjoiMjQ2NzI1NDU2NiJ9.Nk2wyIb37cnzwtazw3UQU4CWC3caY6pBqfIb5j0YQzo',
    'wikibrokercode': '3837527770',
    'CountryCode': '356',
    'LanguageCode': 'en',
    'PreferredLanguageCode': 'en',
    'web-version': '5',
    'BasicData': '999,0,100,0,0,4435bbe86d160fd824938a1d1fc85a58,0',
    'Routes': 'simulationtradetemp$klines',
    'Origin': 'https://wttplay.worldtradingtournament.com',
    'Connection': 'keep-alive',
    'Referer': 'https://wttplay.worldtradingtournament.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=0',
    'TE': 'trailers'
}

# Test with SXPUSD symbol from your example
test_symbol_id = "619557173490693"

import time
end_timestamp = int(time.time() * 1000)

payload = {
    "symbol": test_symbol_id,
    "period": "1h",
    "limit": 300,
    "end_timestamp": end_timestamp
}

print("Testing API connection...")
print(f"URL: {API_BASE_URL}")
print(f"Symbol: {test_symbol_id} (SXPUSD)")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(
        API_BASE_URL,
        headers=API_HEADERS,
        json=payload,
        timeout=10
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✓ Request successful!")
        
        # Try to parse JSON
        try:
            data = response.json()
            print("\n=== Response JSON Structure ===")
            print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
            
            # Try to navigate the structure
            print("\n=== Navigating Response ===")
            if isinstance(data, dict):
                print(f"Top-level keys: {list(data.keys())}")
                
                if 'data' in data:
                    print(f"data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else type(data['data'])}")
                    
                    if isinstance(data['data'], dict) and 'simulationtradetemp' in data['data']:
                        print(f"simulationtradetemp keys: {list(data['data']['simulationtradetemp'].keys())}")
                        
                        if 'klines' in data['data']['simulationtradetemp']:
                            print(f"klines keys: {list(data['data']['simulationtradetemp']['klines'].keys())}")
                            
                            if 'data' in data['data']['simulationtradetemp']['klines']:
                                klines_data = data['data']['simulationtradetemp']['klines']['data']
                                print(f"klines.data keys: {list(klines_data.keys()) if isinstance(klines_data, dict) else type(klines_data)}")
                                
                                if isinstance(klines_data, dict) and 'list' in klines_data:
                                    klines_list = klines_data['list']
                                    print(f"klines.data.list: {len(klines_list)} items")
                                    if klines_list:
                                        print(f"First item: {klines_list[0]}")
        except json.JSONDecodeError:
            print("✗ Response is not valid JSON")
            print(f"Response text: {response.text[:500]}")
    else:
        print(f"\n✗ Request failed with status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("✗ Request timed out")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
