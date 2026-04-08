#!/bin/bash
# Installation script for genPiHub

set -e

echo "========================================="
echo "  genPiHub Installation"
echo "========================================="
echo ""

# Check conda environment
if [[ "$CONDA_DEFAULT_ENV" != "genesislab" ]]; then
    echo "❌ Error: Please activate genesislab environment first"
    echo "   Run: conda activate genesislab"
    exit 1
fi

echo "✓ Conda environment: $CONDA_DEFAULT_ENV"

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [[ ! -f "setup.py" ]]; then
    echo "❌ Error: setup.py not found"
    echo "   Please run this script from src/genPiHub directory"
    exit 1
fi

echo ""
echo "Installing genPiHub in editable mode..."
pip install -e .

echo ""
echo "========================================="
echo "  Installation Complete! ✨"
echo "========================================="
echo ""
echo "Verify installation:"
echo "  python -c 'import genPiHub; print(genPiHub.__version__)'"
echo ""
echo "Run tests:"
echo "  python scripts/check_amo_setup.py"
echo "  python scripts/test_amo_policy.py"
echo "  python scripts/play_amo_genesis_hub.py --viewer"
echo ""
