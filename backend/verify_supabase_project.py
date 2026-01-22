"""Verify Supabase project and connection string format."""
import re

print("=" * 60)
print("Supabase Connection String Verification")
print("=" * 60)

print("\nPlease check the following in your Supabase Dashboard:\n")

print("1. PROJECT STATUS")
print("   - Go to: https://supabase.com/dashboard")
print("   - Check if your project shows as 'Active' (not 'Paused')")
print("   - Paused projects cannot accept connections\n")

print("2. CONNECTION STRING LOCATION")
print("   - Settings > Database > Connection Pooling")
print("   - Look for 'Session mode' connection string")
print("   - Copy the ENTIRE string\n")

print("3. CONNECTION STRING FORMATS")
print("   Common formats you might see:\n")
print("   Format A (Connection Pooling):")
print("   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
print("\n   Format B (Direct Connection):")
print("   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
print("\n   Format C (Alternative Pooling):")
print("   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[REGION].pooler.supabase.com:6543/postgres\n")

print("4. WHAT TO CHECK")
print("   ✓ Hostname should end in .supabase.co or .pooler.supabase.com")
print("   ✓ Port should be 5432 (direct) or 6543 (pooling)")
print("   ✓ Project reference should match your project ID")
print("   ✓ Password should match your database password\n")

print("5. CURRENT CONNECTION STRING ISSUE")
print("   Your current hostname: db.useobjigmlpabgrnufav.supabase.co")
print("   This hostname cannot be resolved by DNS")
print("   This suggests:")
print("   - The project reference might be incorrect")
print("   - The project might be paused")
print("   - The connection string format might be wrong\n")

print("6. NEXT STEPS")
print("   a) Verify project is Active in Supabase dashboard")
print("   b) Get the connection string from Connection Pooling section")
print("   c) Make sure you're copying the FULL string")
print("   d) Try the connection pooling URL (port 6543) first")
print("   e) If that doesn't work, try direct connection (port 5432)\n")

print("7. TEST YOUR CONNECTION STRING")
print("   Once you have the correct string, test it with:")
print("   python test_db_connection.py")
print("   OR")
print("   python update_db_connection.py 'YOUR_CONNECTION_STRING'\n")

# Check current .env
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    current_url = os.getenv("DATABASE_URL", "")
    
    if current_url:
        # Extract hostname
        if "@" in current_url:
            hostname = current_url.split("@")[1].split("/")[0].split(":")[0]
            print("=" * 60)
            print("CURRENT CONNECTION STRING ANALYSIS")
            print("=" * 60)
            print(f"\nHostname: {hostname}")
            
            # Check format
            if "pooler.supabase.com" in hostname:
                print("✓ Using connection pooling format")
            elif ".supabase.co" in hostname:
                print("✓ Using direct connection format")
            else:
                print("⚠ Unrecognized hostname format")
            
            # Check port
            if ":6543" in current_url:
                print("✓ Using port 6543 (connection pooling)")
            elif ":5432" in current_url:
                print("✓ Using port 5432 (direct connection)")
            
            # Check password encoding
            if "%" in current_url:
                print("✓ Password appears to be URL-encoded")
            else:
                print("⚠ Password might need URL-encoding if it has special chars")
except Exception as e:
    print(f"\nCould not analyze current connection string: {e}")

print("\n" + "=" * 60)
