# How to Get Your Supabase Connection String

## Step-by-Step Instructions

### Step 1: Access Supabase Dashboard
1. Go to **https://supabase.com/dashboard**
2. Log in to your account
3. Make sure your project is **active** (not paused)

### Step 2: Navigate to Database Settings
1. In the left sidebar, click **Settings** (gear icon)
2. Click **Database** in the settings menu
3. You should see several sections including:
   - Connection info
   - Connection pooling
   - Database password

### Step 3: Get Connection Pooling String (Recommended)
1. Scroll down to the **"Connection pooling"** section
2. You'll see connection strings for different modes:
   - **Session mode** (recommended for most apps)
   - **Transaction mode**
3. Click the **copy icon** next to the connection string
4. The format should be:
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   OR
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@[REGION].pooler.supabase.com:6543/postgres
   ```

### Step 4: Verify Your Database Password
1. In the same Database settings page
2. Look for **"Database password"** section
3. If you don't remember it, you can **reset it** (this will require restarting your database)
4. Make sure the password in your connection string matches this password

### Step 5: Check Connection Pooling Status
1. Make sure **Connection Pooling** is **enabled** for your project
2. Some free tier projects might have restrictions
3. If pooling isn't available, use the **Direct connection** string (port 5432)

### Step 6: Alternative - Direct Connection
If connection pooling doesn't work:
1. Look for **"Connection string"** section (not pooling)
2. Select **"URI"** format
3. Copy the connection string
4. Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`

### Step 7: Important Notes

**Password Special Characters:**
If your password contains special characters, you may need to URL-encode them:
- `!` → `%21`
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`

**Example:**
If your password is `MyPass!123`, the encoded version is `MyPass%21123`

**Connection String Format:**
```
postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]
```

### Step 8: Test Your Connection String
Once you have the connection string:
1. Update your `.env` file with the new `DATABASE_URL`
2. Run the test script: `python test_db_connection.py`
3. Or test directly: `python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); print('✅ Connected!'); conn.close()"`

## Common Issues

### Issue: "could not translate host name"
- **Solution**: Verify the hostname is correct from Supabase dashboard
- Check if your project is active (not paused)
- Try the connection pooling URL instead of direct connection

### Issue: "password authentication failed"
- **Solution**: Verify the password matches your database password in Supabase
- Reset the password if needed
- URL-encode special characters in the password

### Issue: "connection timeout"
- **Solution**: Check your internet connection
- Verify Supabase project is not paused
- Check if your IP needs to be whitelisted (usually not needed)

### Issue: "too many connections"
- **Solution**: Use connection pooling (port 6543) instead of direct connection (port 5432)
- Connection pooling handles multiple connections better

## Next Steps After Connection Works

Once the connection test succeeds:
1. Run database migrations: `alembic upgrade head`
2. Test the full application
3. Continue with Phase 1 development
