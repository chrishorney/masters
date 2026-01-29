# Connection Pool Exhaustion Fix

## Problem

The background sync job was experiencing connection pool exhaustion errors from Supabase:

```
MaxClientsInSessionMode: max clients reached - in Session mode max clients are limited to pool_size
```

This error was blocking the automatic sync every 5 minutes, even when the sync was enabled.

## Root Causes

1. **No connection pool limits**: The database engine didn't have pool size limits configured, allowing unlimited connection attempts
2. **Unnecessary `db.refresh()` calls**: The `save_score_snapshot` method was calling `db.refresh()` which required an additional connection from the pool
3. **No retry logic**: When connection pool errors occurred, the job would fail immediately without retrying
4. **Session management**: Sessions weren't being closed promptly, holding connections longer than necessary

## Solutions Implemented

### 1. Connection Pool Configuration (`backend/app/database.py`)

Added conservative pool size limits to prevent exhaustion:

```python
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,              # Maintain 5 connections in pool
    max_overflow=10,          # Allow up to 10 additional connections
    pool_recycle=3600,        # Recycle connections after 1 hour
    pool_timeout=30,          # Timeout when getting connection
    echo=settings.environment == "development"
)
```

**Why these values?**
- Supabase connection pooler typically allows 15 connections in session mode
- `pool_size=5` + `max_overflow=10` = maximum 15 connections (matches Supabase limit)
- `pool_recycle=3600` prevents stale connections
- `pool_timeout=30` prevents indefinite waiting

### 2. Removed Unnecessary `db.refresh()` (`backend/app/services/data_sync.py`)

Changed from:
```python
self.db.add(snapshot)
self.db.commit()
self.db.refresh(snapshot)  # ❌ Unnecessary, uses extra connection
```

To:
```python
self.db.add(snapshot)
self.db.commit()
self.db.flush()  # ✅ Ensures ID is available without full refresh
```

### 3. Retry Logic with Exponential Backoff (`backend/app/services/background_jobs.py`)

Added retry mechanism specifically for connection pool errors:

- Detects connection pool errors by checking error message
- Retries up to 3 times with exponential backoff (2s, 4s, 8s)
- Creates fresh database sessions for each retry attempt
- Closes sessions promptly to free up connections

### 4. Improved Session Management

- Background job now closes the outer session before starting sync/calc operations
- Each retry attempt creates and closes its own session
- Added try/except around `db.close()` to handle already-closed sessions gracefully

## Prevention

These changes ensure:

1. **Connection pool limits** prevent exceeding Supabase's maximum connections
2. **Retry logic** handles transient connection pool exhaustion gracefully
3. **Efficient session management** minimizes connection hold time
4. **Better error handling** provides clear logging for connection issues

## Monitoring

Watch for these log messages:

- `Connection pool error (attempt X/3). Retrying in Y seconds...` - Normal retry behavior
- `Connection pool exhausted after retries` - Indicates persistent issue, may need investigation
- `MaxClientsInSessionMode` - Should no longer appear with these fixes

## Future Improvements

If connection pool issues persist:

1. **Reduce pool size further** if still hitting limits
2. **Implement connection pooling at application level** (e.g., using PgBouncer)
3. **Add connection pool metrics** to monitor usage
4. **Consider using Supabase's transaction mode** instead of session mode (if supported)
