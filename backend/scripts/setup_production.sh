#!/bin/bash
# Production setup script

echo "Setting up production environment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp env.template .env
    echo "⚠️  Please edit .env with your production values"
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Verify setup
echo "Verifying setup..."
python -c "
from app.database import SessionLocal
from app.models import Tournament
db = SessionLocal()
try:
    count = db.query(Tournament).count()
    print(f'✓ Database connected. Found {count} tournaments.')
    db.close()
except Exception as e:
    print(f'✗ Database error: {e}')
    exit(1)
"

echo ""
echo "Setup complete!"
echo "Next steps:"
echo "1. Edit .env with production values"
echo "2. Test API: uvicorn app.main:app --reload"
echo "3. Visit http://localhost:8000/docs to verify"
