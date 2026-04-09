#!/bin/bash
# Quick test for AMO on USD terrain
# This script validates the integration without requiring a full run

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../../../.."

cd "$PROJECT_ROOT"

echo "======================================================================"
echo "🧪 AMO on USD Terrain - Quick Test"
echo "======================================================================"
echo ""

# Check USD file
USD_FILE="third_party/genPiHub/data/assets/CWDL_LW_Assets_20260310/Scene.usd"
if [ ! -f "$USD_FILE" ]; then
    echo "❌ ERROR: USD file not found: $USD_FILE"
    echo ""
    echo "Please ensure the Scene.usd file exists."
    exit 1
fi
echo "✅ USD file found: $USD_FILE"

# Check AMO models
AMO_MODEL="data/AMO/amo_jit.pt"
if [ ! -f "$AMO_MODEL" ]; then
    echo "⚠️  WARNING: AMO model not found: $AMO_MODEL"
    echo "   The script will fail without AMO models."
    echo "   This is OK for checking the integration code."
fi

echo ""
echo "======================================================================"
echo "Test 1: Headless Mode (50 steps)"
echo "======================================================================"
echo ""

python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --headless \
    --num-envs 1 \
    --max-steps 50 \
    --print-every 10

TEST1_RESULT=$?

echo ""
echo "======================================================================"
echo "📊 Test Results"
echo "======================================================================"
echo ""

if [ $TEST1_RESULT -eq 0 ]; then
    echo "✅ Headless test: PASSED"
    echo ""
    echo "🎉 AMO on USD terrain integration is working!"
    echo ""
    echo "Next steps:"
    echo "  1. Try with viewer:"
    echo "     python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer"
    echo ""
    echo "  2. Enable interactive control:"
    echo "     python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer --interactive"
    echo ""
    echo "  3. Try multiple environments:"
    echo "     python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer --num-envs 4"
    echo ""
    exit 0
else
    echo "❌ Headless test: FAILED"
    echo ""
    echo "Please check the error messages above."
    exit 1
fi
