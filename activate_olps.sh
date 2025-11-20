#!/usr/bin/env zsh
# Activate the olps environment
# Usage: source activate_olps.sh

# Initialize Homebrew
eval "$(/opt/homebrew/bin/brew shellenv)"

# Initialize pyenv
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Activate olps explicitly
pyenv activate olps 2>/dev/null || pyenv shell olps

# Verify olps is active
PYTHON_PATH=$(python -c "import sys; print(sys.executable)" 2>/dev/null)
if [[ "$PYTHON_PATH" == *"/olps/"* ]]; then
    echo "✓ olps environment activated successfully"
    echo "  Python: $(python --version 2>&1)"
    echo "  Path: $PYTHON_PATH"
else
    echo "⚠ Warning: olps environment may not be active"
    echo "  Current Python: $(which python 2>&1 || echo 'not found')"
    echo "  Try running: pyenv activate olps"
fi
