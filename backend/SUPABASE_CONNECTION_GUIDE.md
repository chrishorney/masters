# Supabase Connection String Guide

## Step-by-Step Instructions

### 1. Log into Supabase
- Go to https://supabase.com/dashboard
- Log in to your account
- Select your project

### 2. Navigate to Database Settings
- Click on **Settings** (gear icon in left sidebar)
- Click on **Database** in the settings menu

### 3. Find Connection String
You'll see several connection options. We need the **Connection Pooling** string.

### 4. Choose Connection Pooling (Recommended)
- Look for **"Connection pooling"** section
- Select **"Session mode"** (or Transaction mode - both work)
- Copy the connection string

The format should look like:
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

### 5. Important Notes:
- **Port 6543** = Connection pooling (recommended for applications)
- **Port 5432** = Direct connection (can have connection limits)
- The password in the connection string should be your **database password**
- If your password has special characters, they may need URL encoding

### 6. URL Encoding Special Characters
If your password contains special characters, they need to be URL encoded:
- `!` becomes `%21`
- `@` becomes `%40`
- `#` becomes `%23`
- `$` becomes `%24`
- `%` becomes `%25`
- `&` becomes `%26`
- `*` becomes `%2A`
- `+` becomes `%2B`
- `=` becomes `%3D`
- `?` becomes `%3F`

### 7. Test Your Connection String
Once you have the connection string, we'll test it to make sure it works.
