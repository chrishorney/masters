# Testing the Ranking Snapshots Migration

## Step-by-Step Instructions

### 1. Open Terminal
- On Mac: Press `Cmd + Space`, type "Terminal", press Enter
- Or use the terminal in your IDE (Cursor)

### 2. Navigate to the Backend Directory
```bash
cd "/Volumes/External HD/masters/backend"
```

### 3. Activate the Virtual Environment
```bash
source venv/bin/activate
```

You should see `(venv)` appear at the beginning of your command prompt, like:
```
(venv) chrishorney@Chriss-MacBook-Pro backend %
```

### 4. Verify Database Connection
Make sure your `.env` file in the `backend` directory has the correct database connection string. The migration will use this connection.

### 5. Run the Migration
```bash
alembic upgrade head
```

### 6. What to Expect

**If successful**, you'll see output like:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade fd7c075d609b -> a1b2c3d4e5f6, add_ranking_snapshots_table
```

**If there's an error**, you'll see error messages that we can troubleshoot.

### 7. Verify the Table Was Created

You can verify the table exists by checking your database:
- In Supabase: Go to Table Editor → Look for `ranking_snapshots` table
- Or run this Python command:
```bash
python3 -c "from app.database import engine; from sqlalchemy import inspect; inspector = inspect(engine); print('Tables:', inspector.get_table_names())"
```

### 8. Check Migration Status
To see what migrations have been applied:
```bash
alembic current
```

To see all available migrations:
```bash
alembic history
```

## Troubleshooting

### If you get "command not found: alembic"
- Make sure the virtual environment is activated (you should see `(venv)` in your prompt)
- Try: `pip install alembic` (though it should already be in requirements.txt)

### If you get database connection errors
- Check your `.env` file has the correct `DATABASE_URL`
- Make sure your database is accessible

### If the migration says "already applied"
- That's fine! It means the migration was already run
- You can check with: `alembic current`

## Next Steps

Once the migration is successful, we can move to Chunk 2: Adding the snapshot capture logic.
