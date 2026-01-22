"""Test database connection with different configurations."""
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import psycopg2
from psycopg2 import OperationalError

load_dotenv()

print("=" * 60)
print("Database Connection Test")
print("=" * 60)

# Get current connection string
current_url = os.getenv("DATABASE_URL", "")
print(f"\nCurrent DATABASE_URL format:")
if current_url:
    # Hide password in display
    display_url = current_url.split("@")[0].split(":")[0] + ":***@" + "@".join(current_url.split("@")[1:])
    print(f"  {display_url}")
else:
    print("  No DATABASE_URL found in .env")
    exit(1)

print("\n" + "=" * 60)
print("Testing Connection...")
print("=" * 60)

# Test 1: Direct connection (port 5432)
print("\n1. Testing Direct Connection (port 5432)...")
try:
    conn = psycopg2.connect(current_url, connect_timeout=10)
    conn.close()
    print("   ✅ Direct connection successful!")
    direct_works = True
except OperationalError as e:
    print(f"   ❌ Direct connection failed: {e}")
    direct_works = False
except Exception as e:
    print(f"   ❌ Error: {e}")
    direct_works = False

# Test 2: Try connection pooling (port 6543)
print("\n2. Testing Connection Pooling (port 6543)...")
pooling_url = current_url.replace(":5432", ":6543")
if "db." in pooling_url:
    # Convert db.xxx.supabase.co to aws-0-xxx.pooler.supabase.com format
    # This is a simplified attempt - actual format depends on Supabase region
    pooling_url = pooling_url.replace("db.", "aws-0-").replace(".supabase.co:6543", ".pooler.supabase.com:6543")
    
try:
    conn = psycopg2.connect(pooling_url, connect_timeout=10)
    conn.close()
    print("   ✅ Connection pooling successful!")
    print(f"   Use this URL: {pooling_url.split('@')[0].split(':')[0]}:***@{'@'.join(pooling_url.split('@')[1:])}")
    pooling_works = True
except OperationalError as e:
    print(f"   ❌ Connection pooling failed: {e}")
    pooling_works = False
except Exception as e:
    print(f"   ❌ Error: {e}")
    pooling_works = False

# Test 3: Try with URL-encoded password
print("\n3. Testing with URL-encoded password...")
if "!" in current_url or "@" in current_url or "#" in current_url:
    # Extract password and encode it
    try:
        # Parse the URL
        parts = current_url.split("@")
        auth_part = parts[0]
        rest = "@".join(parts[1:])
        
        if ":" in auth_part:
            user_pass = auth_part.split("//")[1]
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                encoded_password = quote_plus(password)
                encoded_url = current_url.replace(f":{password}@", f":{encoded_password}@")
                
                try:
                    conn = psycopg2.connect(encoded_url, connect_timeout=10)
                    conn.close()
                    print("   ✅ URL-encoded password connection successful!")
                    print(f"   Use this URL format with encoded password")
                    encoded_works = True
                except Exception as e:
                    print(f"   ❌ URL-encoded connection failed: {e}")
                    encoded_works = False
            else:
                print("   ⚠️  Could not parse password from URL")
                encoded_works = False
        else:
            print("   ⚠️  Could not parse authentication from URL")
            encoded_works = False
    except Exception as e:
        print(f"   ❌ Error encoding password: {e}")
        encoded_works = False
else:
    print("   ⚠️  No special characters detected in password")
    encoded_works = None

# Summary
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
if direct_works:
    print("✅ Direct connection (5432) works - you can use this")
elif pooling_works:
    print("✅ Connection pooling (6543) works - recommended for production")
elif encoded_works:
    print("✅ URL-encoded password works - use this format")
else:
    print("❌ None of the connection methods worked")
    print("\nTroubleshooting steps:")
    print("1. Verify your database password in Supabase dashboard")
    print("2. Check if your IP needs to be whitelisted (Settings > Database > Connection Pooling)")
    print("3. Try getting the connection string from Supabase dashboard again")
    print("4. Make sure you're using the 'Connection Pooling' string, not 'Direct Connection'")
    print("\nGet the connection string from:")
    print("  Supabase Dashboard > Settings > Database > Connection Pooling")
