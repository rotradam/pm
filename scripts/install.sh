#!/usr/bin/env bash
# Install dependencies into the olps environment

set -e

echo "Installing OLPS Dashboard dependencies..."
echo "=========================================="

# Ensure we're using the correct Python from pyenv
if command -v pyenv &> /dev/null; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -e .

echo ""
echo "✓ Installation complete!"
echo ""
echo "To verify:"
echo "  python -c 'import backend; print(backend.__version__)'"
