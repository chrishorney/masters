#!/bin/bash
# Script to sync tournament data and generate test CSV

TOURNAMENT_ID=2
API_URL="https://masters-production.up.railway.app"
YEAR=2026
# Masters Tournament ID in Slash Golf API (you may need to update this)
# Common Masters IDs: 470 (2024), 470 (2025), etc. - check Slash Golf API docs
TOURN_ID="${TOURN_ID:-470}"  # Default to 470, can override with env var

echo "================================================================================"
echo "SYNC TOURNAMENT AND GENERATE TEST CSV"
echo "================================================================================"
echo "Database Tournament ID: $TOURNAMENT_ID"
echo "Slash Golf Tournament ID: $TOURN_ID"
echo "API URL: $API_URL"
echo "Year: $YEAR"
echo "================================================================================"
echo ""

# Step 1: Sync tournament data
echo "📥 Step 1: Syncing tournament data..."
echo "Calling: $API_URL/api/tournament/sync?year=$YEAR&tourn_id=$TOURN_ID"
SYNC_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_URL/api/tournament/sync?year=$YEAR&tourn_id=$TOURN_ID")
HTTP_CODE=$(echo "$SYNC_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESPONSE_BODY=$(echo "$SYNC_RESPONSE" | sed '/HTTP_CODE/d')
echo "HTTP Status: $HTTP_CODE"
echo "Response: $RESPONSE_BODY"
echo ""

# Check if sync was successful
if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | grep -q "tournament_id"; then
    echo "✅ Tournament synced successfully"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "⚠️  Got 200 but response doesn't look right: $RESPONSE_BODY"
    echo "Continuing anyway..."
else
    echo "❌ Tournament sync failed (HTTP $HTTP_CODE)"
    echo "Response: $RESPONSE_BODY"
    echo ""
    echo "Trying to check if tournament exists..."
    curl -s "$API_URL/api/tournament/2" | head -20
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
