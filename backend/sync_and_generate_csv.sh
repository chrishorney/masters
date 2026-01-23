#!/bin/bash
# Script to sync tournament data and generate test CSV

TOURNAMENT_ID=2
API_URL="https://masters-production.up.railway.app"
YEAR=2026

echo "================================================================================"
echo "SYNC TOURNAMENT AND GENERATE TEST CSV"
echo "================================================================================"
echo "Tournament ID: $TOURNAMENT_ID"
echo "API URL: $API_URL"
echo "Year: $YEAR"
echo "================================================================================"
echo ""

# Step 1: Sync tournament data
echo "📥 Step 1: Syncing tournament data..."
SYNC_RESPONSE=$(curl -s -X POST "$API_URL/api/tournament/sync?year=$YEAR")
echo "Response: $SYNC_RESPONSE"
echo ""

# Check if sync was successful
if echo "$SYNC_RESPONSE" | grep -q "tournament_id"; then
    echo "✅ Tournament synced successfully"
else
    echo "❌ Tournament sync failed. Response: $SYNC_RESPONSE"
    exit 1
fi

# Wait a moment for data to be available
echo "⏳ Waiting 2 seconds for data to be available..."
sleep 2

# Step 2: Generate CSV
echo ""
echo "📝 Step 2: Generating test CSV..."
python3 generate_test_csv.py \
  --tournament-id $TOURNAMENT_ID \
  --api-url $API_URL

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ CSV generated successfully!"
    echo "📄 File: test_entries.csv"
    echo ""
    echo "Next step: Import the CSV"
    echo "curl -X POST \"$API_URL/api/admin/import/entries\" \\"
    echo "  -F \"tournament_id=$TOURNAMENT_ID\" \\"
    echo "  -F \"file=@test_entries.csv\""
else
    echo "❌ CSV generation failed"
    exit 1
fi
