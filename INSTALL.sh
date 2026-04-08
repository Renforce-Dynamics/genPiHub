#!/bin/bash
# Installation script for genPiHub

set -e

echo "========================================="
echo "  genPiHub Installation"
echo "========================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
if [[ ! -f "setup.py" ]]; then
    echo "❌ Error: setup.py not found"
    echo "   Please run this script from src/genPiHub directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check current environment
if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    echo "✓ Conda environment: $CONDA_DEFAULT_ENV"
else
    echo "⚠️  Warning: Not in a conda environment"
fi

# Check dependencies
echo ""
echo "Checking dependencies..."

# Check PyTorch
if python -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python -c "import torch; print(torch.__version__)")
    echo "✓ PyTorch: $TORCH_VERSION"
else
    echo "❌ PyTorch not found"
    echo "   Install: pip install torch"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Genesis
if python -c "import genesis" 2>/dev/null; then
    echo "✓ Genesis installed"
else
    echo "⚠️  Genesis not found (optional for some features)"
fi

# Install genPiHub
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
echo "  python scripts/amo/check_amo_setup.py"
echo "  python scripts/amo/test_amo_policy.py"
echo "  python scripts/amo/play_amo.py --viewer"
echo ""
