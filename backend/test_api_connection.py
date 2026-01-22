"""Quick test script to verify Slash Golf API connection."""
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

api_key = os.getenv("SLASH_GOLF_API_KEY")
api_host = os.getenv("SLASH_GOLF_API_HOST", "live-golf-data.p.rapidapi.com")

if not api_key:
    print("❌ SLASH_GOLF_API_KEY not found in .env file")
    exit(1)

print(f"Testing connection to {api_host}...")
print(f"API Key: {api_key[:10]}...{api_key[-5:]}")

# Test with a simple endpoint - get schedule
url = "https://live-golf-data.p.rapidapi.com/schedule"
headers = {
    "x-rapidapi-host": api_host,
    "x-rapidapi-key": api_key
}
params = {
    "orgId": "1",
    "year": "2024"
}

try:
    response = httpx.get(url, headers=headers, params=params, timeout=10.0)
    if response.status_code == 200:
        print("✅ API connection successful!")
        data = response.json()
        if "schedule" in data:
            print(f"✅ Found {len(data['schedule'])} tournaments in schedule")
        else:
            print(f"✅ Response received: {list(data.keys())}")
    else:
        print(f"❌ API returned status {response.status_code}")
        print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error connecting to API: {e}")
