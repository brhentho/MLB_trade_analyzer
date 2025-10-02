#!/bin/bash
# Quick test script for MVP

echo "🧪 Testing MLB Trade Analyzer MVP"
echo "=================================="
echo ""

# Start backend
echo "1️⃣ Starting backend..."
cd "$(dirname "$0")"
python3 backend/mvp_main.py &
BACKEND_PID=$!
sleep 3

# Test health endpoint
echo "2️⃣ Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/)
echo "$HEALTH" | python3 -m json.tool
echo ""

# Test evaluation endpoint
echo "3️⃣ Testing trade evaluation..."
echo "   Trade: Yankees get Juan Soto, Padres get Clarke Schmidt + Prospect"
echo ""

curl -s -X POST http://localhost:8000/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{"team_a":"Yankees","team_a_gets":["Juan Soto"],"team_b":"Padres","team_b_gets":["Clarke Schmidt","Top Prospect"],"context":"Yankees need power, Padres rebuilding"}' \
  | python3 -m json.tool

echo ""
echo "4️⃣ Stopping backend..."
kill $BACKEND_PID

echo ""
echo "✅ Test complete!"
echo ""
echo "💡 If you see 'insufficient_quota' error:"
echo "   → Add billing at https://platform.openai.com/account/billing"
echo "   → Minimum $5 credit"
echo "   → Cost per trade: ~$0.02-0.05"
