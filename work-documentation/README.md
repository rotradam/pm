# Documentation Index

**Date**: 2025-11-16  
**Purpose**: Index of all work documentation  
**Status**: Active

## Documentation Files

### 1. Quick Start Guide
**File**: `2025-11-16_quick-start-guide.md`  
**Purpose**: Get started with the project in 3 steps  
**Target Audience**: New developers, returning after break  
**Key Sections**:
- 3-step quick start
- Project structure overview
- Common commands
- Troubleshooting guide

### 2. Environment Setup
**File**: `2025-11-16_environment-setup.md`  
**Purpose**: Detailed Python environment configuration  
**Target Audience**: Developers setting up new machine, debugging environment issues  
**Key Sections**:
- pyenv and pyenv-virtualenv explanation
- Activation methods (simple and manual)
- Dependency management
- Common issues and solutions

### 3. Backend Architecture & Data Pipeline
**File**: `2025-11-16_backend-architecture-data-pipeline.md`  
**Purpose**: Technical documentation of backend implementation  
**Target Audience**: Developers extending the codebase  
**Key Sections**:
- Strategy interface design
- Universe management
- ISIN→ticker mapping logic
- Price fetcher implementation
- Usage examples and extension guides

## Quick Reference

### Daily Workflow

1. **Start working**:
   ```bash
   cd /Users/royceantonjose/git_rotradam/portfolioManagement
   source activate_olps.sh
   ```

2. **Verify environment**:
   ```bash
   python --version  # Should be 3.11.9
   ```

3. **Run scripts**:
   ```bash
   python scripts/download_data.py
   ```

### Documentation Guidelines

When adding new code or features, create documentation in this folder:

**File naming**: `YYYY-MM-DD_brief-description.md`

**Required sections**:
- Overview
- Key Design Decisions
- How to Use
- How to Extend
- Testing Notes
- Next Steps

**Example**:
```markdown
# Feature Name

**Date**: YYYY-MM-DD
**Component**: What this relates to
**Status**: Implemented/In Progress/Planned

## Overview
Brief description...

## Key Design Decisions
Why was it built this way...

## How to Use
Code examples...

## How to Extend
Instructions for future developers...
```

## Project Status

### Completed ✅
- Python 3.11.9 environment with pyenv
- Backend data layer (universe, mapper, prices)
- Strategy interface (OlpsStrategy, StrategyResult)
- Data pipeline script
- Activation helper script
- Comprehensive documentation

### In Progress ⏳
- Price data download (ready to run)

### Next Up 🎯
- Baseline strategies (EW, BH, CRP)
- Maxblue cost model
- Rebalancing engine
- FastAPI backend
- React dashboard

## Key Files Reference

| File | Purpose | When to Use |
|------|---------|-------------|
| `activate_olps.sh` | Activate environment | Every terminal session |
| `pyproject.toml` | Dependencies | Adding packages |
| `.github/copilot-instructions.md` | AI agent guidance | Setting up AI agents |
| `backend/strategies/base.py` | Strategy interface | Implementing strategies |
| `backend/data/universe.py` | Universe loader | Accessing ETF list |
| `backend/data/mapper.py` | ISIN mapping | Converting ISINs |
| `backend/data/prices.py` | Price fetcher | Downloading data |
| `scripts/download_data.py` | Data pipeline | Initial data download |

## External Resources

- **Research Papers**: `documents/*.pdf`
- **Universe CSV**: `documents/etf_universe_full_clean.csv`
- **PortfolioLab Strategies**: `portfoliolab/*.py` (to be refactored)

## Contact & Support

For questions about:
- **Environment setup**: See `2025-11-16_environment-setup.md`
- **Backend architecture**: See `2025-11-16_backend-architecture-data-pipeline.md`
- **Getting started**: See `2025-11-16_quick-start-guide.md`
- **AI agent configuration**: See `.github/copilot-instructions.md`
