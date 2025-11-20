# Python Environment Setup

**Date**: 2025-11-16  
**Component**: Python environment configuration  
**Status**: Active

## Overview

This document explains the Python environment setup for the OLPS research dashboard project using pyenv and pyenv-virtualenv.

## Key Design Decisions

### 1. Python Version Management

**Decision**: Use pyenv for Python version management and pyenv-virtualenv for environment isolation.

**Rationale**:
- Isolates project dependencies from system Python
- Allows multiple Python versions on the same machine
- Prevents dependency conflicts with other projects
- Compatible with macOS and Homebrew ecosystem

### 2. Python Version

**Decision**: Python 3.11.9

**Rationale**:
- Stable and well-supported version
- Compatible with all required dependencies (pandas, numpy, FastAPI, etc.)
- Good performance for numerical computing
- Long-term support through 2027

### 3. Environment Name

**Decision**: Virtual environment named `olps`

**Rationale**:
- Short and memorable
- Matches project focus (Online Portfolio Selection)
- Easy to type for frequent activation

## How to Use

### Initial Setup (Already Completed)

The environment has been created with:

```bash
# Install Python 3.11.9
pyenv install 3.11.9

# Create virtual environment
pyenv virtualenv 3.11.9 olps

# Set as local environment for this directory
pyenv local olps
```

### Activating the Environment

**Simple Method** (recommended):

```bash
source activate_olps.sh
```

This script will:
- Initialize Homebrew
- Initialize pyenv
- Activate the olps environment
- Verify Python version

**Manual Method** (if activation script fails):

```bash
# Initialize shell environment
eval "$(/opt/homebrew/bin/brew shellenv)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Activate olps
pyenv activate olps
```

### Verifying the Environment

Check that you're using the correct Python:

```bash
python --version
# Should output: Python 3.11.9

which python
# Should output: /Users/[username]/.pyenv/versions/olps/bin/python
```

Your terminal prompt should show `(olps)`:

```
(olps) ➜  portfolioManagement git:(main)
```

### Deactivating the Environment

```bash
pyenv deactivate
```

Or simply close the terminal window.

### Common Issues

**Issue**: Running `pyenv shell <other-version>` deactivates olps

**Solution**: Run `source activate_olps.sh` again to reactivate

**Issue**: Terminal doesn't show `(olps)` prefix

**Cause**: pyenv-virtualenv not properly initialized

**Solution**: Run `source activate_olps.sh` which initializes everything

**Issue**: `pyenv: command not found`

**Cause**: Homebrew or pyenv not in PATH

**Solution**: Use `activate_olps.sh` which handles PATH setup

## How to Extend

### Adding New Dependencies

1. Activate the environment:
   ```bash
   source activate_olps.sh
   ```

2. Install packages:
   ```bash
   pip install <package-name>
   ```

3. Update `pyproject.toml`:
   ```toml
   [project]
   dependencies = [
       "existing-package>=1.0.0",
       "new-package>=2.0.0",  # Add here
   ]
   ```

4. Reinstall in development mode:
   ```bash
   pip install -e .
   ```

### Creating a New Environment

If you need to recreate the environment:

```bash
# Delete old environment
pyenv virtualenv-delete olps

# Create new environment
pyenv virtualenv 3.11.9 olps

# Set as local environment
pyenv local olps

# Install dependencies
pip install -e .
```

### Permanent Shell Activation

To avoid running `source activate_olps.sh` every time, add to `~/.zshrc`:

```bash
# Initialize Homebrew (MUST be first)
eval "$(/opt/homebrew/bin/brew shellenv)"

# Initialize pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Then restart your terminal or run:
```bash
source ~/.zshrc
```

## Testing Notes

### Environment Status

- ✅ Python 3.11.9 installed via pyenv
- ✅ Virtual environment `olps` created
- ✅ `.python-version` file in project root
- ✅ All dependencies installed via `pip install -e .`
- ✅ Activation script `activate_olps.sh` working

### Installed Packages

Core dependencies (see `pyproject.toml`):
- pandas 2.3.3
- numpy 2.3.4
- yfinance 0.2.66
- pydantic 2.12.4
- fastapi 0.121.2
- uvicorn 0.34.0
- sqlalchemy 2.0.44
- alembic 1.15.5
- pyarrow 22.0.0
- python-dotenv 1.0.1
- requests 2.32.4

## Next Steps

1. Always activate environment before working: `source activate_olps.sh`
2. Run data download pipeline: `python scripts/download_data.py`
3. Implement baseline strategies
4. Build cost model and rebalancing engine

## File Structure

```
portfolioManagement/
├── activate_olps.sh           # Environment activation script
├── .python-version            # pyenv local environment marker (auto-created)
├── pyproject.toml             # Dependency manifest
└── work-documentation/
    └── 2025-11-16_environment-setup.md  # This file
```
