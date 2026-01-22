"""Test multiple connection string formats."""
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import quote_plus

load_dotenv()

current_url = os.getenv("DATABASE_URL", "")
print("=" * 60)
print("Testing Multiple Connection String Formats")
print("=" * 60)

if not current_url:
    print("❌ No DATABASE_URL found in .env")
    exit(1)

# Parse current URL
try:
    # Extract components
    if "@" in current_url:
        auth_part = current_url.split("@")[0]
        rest = "@".join(current_url.split("@")[1:])
        
        if "//" in auth_part:
            user_pass = auth_part.split("//")[1]
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                host_port_db = rest
                
                # Extract hostname and port
                if ":" in host_port_db:
                    hostname = host_port_db.split(":")[0]
                    port_db = host_port_db.split(":", 1)[1]
                    if "/" in port_db:
                        port = port_db.split("/")[0]
                        database = port_db.split("/", 1)[1]
                    else:
                        port = port_db
                        database = "postgres"
                else:
                    hostname = host_port_db.split("/")[0]
                    port = "5432"
                    database = host_port_db.split("/", 1)[1] if "/" in host_port_db else "postgres"
                
                print(f"\nParsed connection details:")
                print(f"  User: {user}")
                print(f"  Password: {'*' * len(password)}")
                print(f"  Hostname: {hostname}")
                print(f"  Port: {port}")
                print(f"  Database: {database}")
                
                # Extract project reference if possible
                project_ref = None
                if "db." in hostname and ".supabase.co" in hostname:
                    project_ref = hostname.replace("db.", "").replace(".supabase.co", "")
                    print(f"  Project Reference: {project_ref}")
                
                # Test different formats
                formats_to_test = []
                
                # Format 1: Current format (direct connection)
                formats_to_test.append(("Current (Direct)", current_url))
                
                # Format 2: URL-encoded password
                encoded_password = quote_plus(password)
                encoded_url = f"postgresql://{user}:{encoded_password}@{hostname}:{port}/{database}"
                formats_to_test.append(("URL-encoded password", encoded_url))
                
                # Format 3: Connection pooling (if we have project ref)
                if project_ref:
                    # Try different pooling formats
                    pooling_formats = [
                        f"postgresql://postgres.{project_ref}:{password}@aws-0-us-east-1.pooler.supabase.com:6543/{database}",
                        f"postgresql://postgres.{project_ref}:{password}@us-east-1.pooler.supabase.com:6543/{database}",
                        f"postgresql://postgres.{project_ref}:{encoded_password}@aws-0-us-east-1.pooler.supabase.com:6543/{database}",
                        f"postgresql://postgres.{project_ref}:{encoded_password}@us-east-1.pooler.supabase.com:6543/{database}",
                    ]
                    for i, pf in enumerate(pooling_formats, 1):
                        formats_to_test.append((f"Pooling Format {i}", pf))
                
                print("\n" + "=" * 60)
                print("Testing Connection Formats")
                print("=" * 60)
                
                success = False
                for name, test_url in formats_to_test:
                    print(f"\nTesting: {name}")
                    try:
                        conn = psycopg2.connect(test_url, connect_timeout=10)
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        conn.close()
                        print(f"  ✅ SUCCESS! This format works!")
                        print(f"  Use this connection string:")
                        print(f"  {test_url.split('@')[0]}:***@{'@'.join(test_url.split('@')[1:])}")
                        success = True
                        break
                    except psycopg2.OperationalError as e:
                        error_msg = str(e).lower()
                        if "could not translate host name" in error_msg:
                            print(f"  ❌ DNS resolution failed")
                        elif "password authentication failed" in error_msg:
                            print(f"  ❌ Password authentication failed")
                        elif "timeout" in error_msg:
                            print(f"  ❌ Connection timeout")
                        else:
                            print(f"  ❌ {e}")
                    except Exception as e:
                        print(f"  ❌ {type(e).__name__}: {e}")
                
                if not success:
                    print("\n" + "=" * 60)
                    print("❌ None of the formats worked")
                    print("=" * 60)
                    print("\nPlease verify in Supabase Dashboard:")
                    print("1. Go to Settings > Database > Connection Pooling")
                    print("2. Copy the EXACT connection string shown there")
                    print("3. Make sure the project is Active (not Paused)")
                    print("4. Verify the project reference matches")
                    
            else:
                print("❌ Could not parse user:password from connection string")
        else:
            print("❌ Could not parse connection string format")
    else:
        print("❌ Connection string format invalid (missing @)")
        
except Exception as e:
    print(f"❌ Error parsing connection string: {e}")
    print(f"Current URL: {current_url[:50]}...")
