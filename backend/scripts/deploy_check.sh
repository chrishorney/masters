#!/bin/bash
# Deployment checklist script

echo "=========================================="
echo "Pre-Deployment Checklist"
echo "=========================================="

# Check environment variables
echo ""
echo "1. Checking environment variables..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    
    if grep -q "DATABASE_URL" .env; then
        echo "   ✓ DATABASE_URL is set"
    else
        echo "   ✗ DATABASE_URL is missing"
    fi
    
    if grep -q "SLASH_GOLF_API_KEY" .env; then
        echo "   ✓ SLASH_GOLF_API_KEY is set"
    else
        echo "   ✗ SLASH_GOLF_API_KEY is missing"
    fi
else
    echo "   ✗ .env file not found"
fi

# Check database connection
echo ""
echo "2. Testing database connection..."
python -c "
from app.database import SessionLocal
try:
    db = SessionLocal()
    db.execute('SELECT 1')
    db.close()
    print('   ✓ Database connection successful')
except Exception as e:
    print(f'   ✗ Database connection failed: {e}')
"

# Check migrations
echo ""
echo "3. Checking database migrations..."
alembic current
if [ $? -eq 0 ]; then
    echo "   ✓ Migrations are up to date"
else
    echo "   ⚠ Run 'alembic upgrade head' to apply migrations"
fi

# Check tests
echo ""
echo "4. Running tests..."
pytest tests/ -v --tb=short
if [ $? -eq 0 ]; then
    echo "   ✓ All tests passed"
else
    echo "   ✗ Some tests failed"
fi

# Check API server
echo ""
echo "5. Testing API server startup..."
timeout 5 uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
sleep 2
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "   ✓ API server starts successfully"
    kill $SERVER_PID 2>/dev/null
else
    echo "   ✗ API server failed to start"
    kill $SERVER_PID 2>/dev/null
fi

echo ""
echo "=========================================="
echo "Checklist Complete"
echo "=========================================="
