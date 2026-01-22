"""Helper script to update and test database connection."""
import os
import sys
from pathlib import Path

def update_env_file(connection_string):
    """Update the DATABASE_URL in .env file."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Update DATABASE_URL
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("DATABASE_URL="):
            new_lines.append(f"DATABASE_URL={connection_string}\n")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        # Add it if it doesn't exist
        new_lines.append(f"\nDATABASE_URL={connection_string}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Updated .env file with new DATABASE_URL")
    return True

def test_connection(connection_string):
    """Test the database connection."""
    print("\nTesting connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(connection_string, connect_timeout=10)
        conn.close()
        print("✅ Connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Connection String Updater")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python update_db_connection.py '<connection_string>'")
        print("\nExample:")
        print('  python update_db_connection.py "postgresql://postgres:password@host:5432/postgres"')
        print("\nGet your connection string from:")
        print("  Supabase Dashboard > Settings > Database > Connection Pooling")
        sys.exit(1)
    
    connection_string = sys.argv[1]
    
    # Show masked version
    if "@" in connection_string:
        parts = connection_string.split("@")
        masked = parts[0].split(":")[0] + ":***@" + "@".join(parts[1:])
        print(f"\nConnection string: {masked}")
    else:
        print(f"\nConnection string: {connection_string}")
    
    # Test first
    if test_connection(connection_string):
        # Update .env file
        if update_env_file(connection_string):
            print("\n✅ Success! Your .env file has been updated.")
            print("You can now test with: python test_db_connection.py")
        else:
            print("\n❌ Failed to update .env file")
    else:
        print("\n❌ Connection test failed. Please check:")
        print("  1. Connection string is correct")
        print("  2. Password is correct")
        print("  3. Project is active in Supabase")
        print("  4. Internet connection is working")
        sys.exit(1)
