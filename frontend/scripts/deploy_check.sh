#!/bin/bash
# Frontend deployment checklist

echo "=========================================="
echo "Frontend Pre-Deployment Checklist"
echo "=========================================="

# Check environment variables
echo ""
echo "1. Checking environment variables..."
if [ -f ".env" ]; then
    echo "   ✓ .env file exists"
    
    if grep -q "VITE_API_URL" .env; then
        API_URL=$(grep "VITE_API_URL" .env | cut -d '=' -f2)
        echo "   ✓ VITE_API_URL is set: $API_URL"
    else
        echo "   ✗ VITE_API_URL is missing"
    fi
else
    echo "   ⚠ .env file not found (will use defaults)"
fi

# Check dependencies
echo ""
echo "2. Checking dependencies..."
if [ -d "node_modules" ]; then
    echo "   ✓ node_modules exists"
else
    echo "   ⚠ Run 'npm install' first"
fi

# Build check
echo ""
echo "3. Testing build..."
npm run build
if [ $? -eq 0 ]; then
    echo "   ✓ Build successful"
    if [ -d "dist" ]; then
        SIZE=$(du -sh dist | cut -f1)
        echo "   ✓ Build output: dist/ ($SIZE)"
    fi
else
    echo "   ✗ Build failed"
fi

# Check for TypeScript errors
echo ""
echo "4. Checking TypeScript..."
npx tsc --noEmit
if [ $? -eq 0 ]; then
    echo "   ✓ No TypeScript errors"
else
    echo "   ✗ TypeScript errors found"
fi

echo ""
echo "=========================================="
echo "Checklist Complete"
echo "=========================================="
