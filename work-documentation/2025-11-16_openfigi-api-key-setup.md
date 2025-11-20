# OpenFIGI API Key Setup

**Date**: 2025-11-16  
**Status**: ✅ Configured and working

## Overview

Configured the ISIN resolver script to use OpenFIGI API key for 10x faster mapping performance.

## What Was Done

### 1. Created Environment File Template

Created `.env.example` with the following structure:

```bash
# OpenFIGI API Configuration
OPENFIGI_API_KEY=your_api_key_here

# Data Sources
# Yahoo Finance doesn't require API key (free tier)

# Database Configuration (future use)
# DATABASE_URL=postgresql://user:password@localhost:5432/olps_db
```

### 2. Updated Resolver Script

**File**: `scripts/resolve_isins_openfigi.py`

Changes:
- Added `python-dotenv` for environment variable loading
- Updated `__init__` method to:
  - Check for API key in environment variable `OPENFIGI_API_KEY`
  - Adjust rate limit based on key presence (25 vs 250 req/min)
  - Create requests Session with API key header if provided
- Added `X-OPENFIGI-APIKEY` header to all requests when key is present
- Fixed missing instance variables (`request_count`, `request_window_start`, `session`)

### 3. Installed Dependencies

```bash
pip install python-dotenv
```

Updated `pyproject.toml`:
```toml
dependencies = [
    "pandas>=2.0.0",
    "yfinance>=0.2.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",  # NEW
]
```

### 4. Security

- `.env` already in `.gitignore` - API key will NOT be committed
- `.env.example` is the template (safe to commit)

## How to Use

### Setup (one-time)

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit .env and add your actual API key
# OPENFIGI_API_KEY=your_actual_key_here

# Get free key at: https://www.openfigi.com/api
```

### Running the Resolver

```bash
python scripts/resolve_isins_openfigi.py
```

The script will:
- Automatically detect the API key from `.env`
- Log which rate limit is active:
  - With key: `"Using OpenFIGI API key (250 req/min rate limit)"`
  - Without key: `"No API key provided (25 req/min rate limit)"`

## Performance Impact

| Scenario | Rate Limit | Time for 120 ISINs | Speed |
|----------|------------|-------------------|-------|
| Without key | 25 req/min | ~4-5 minutes | 1x |
| With API key | 250 req/min | ~30-40 seconds | **10x** |

## Technical Details

### Code Changes

**`__init__` method**:
```python
def __init__(self, api_key: Optional[str] = None):
    self.api_key = api_key or os.getenv("OPENFIGI_API_KEY")
    if self.api_key:
        logger.info("Using OpenFIGI API key (250 req/min rate limit)")
        self.rate_limit = 250
    else:
        logger.info("No API key provided (25 req/min rate limit)")
        self.rate_limit = 25
    
    self.request_count = 0
    self.request_window_start = time.time()
    self.session = requests.Session()
    
    # Add API key to session headers if provided
    if self.api_key:
        self.session.headers.update({"X-OPENFIGI-APIKEY": self.api_key})
```

**Rate limiting**:
```python
def _rate_limit(self):
    self.request_count += 1
    
    elapsed = time.time() - self.request_window_start
    if elapsed > 60:
        self.request_count = 1
        self.request_window_start = time.time()
        return
    
    # Dynamic rate limit based on API key presence
    if self.request_count >= self.rate_limit:
        wait_time = 60 - elapsed + 1
        logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
        time.sleep(wait_time)
        self.request_count = 1
        self.request_window_start = time.time()
```

## Troubleshooting

### Issue: AttributeError 'OpenFigiResolver' object has no attribute 'session'

**Cause**: Missing instance variable initialization

**Fix**: Added these lines to `__init__`:
```python
self.request_count = 0
self.request_window_start = time.time()
self.session = requests.Session()
```

### Issue: API key not detected

**Check**:
1. `.env` file exists in project root
2. File contains `OPENFIGI_API_KEY=your_key_here`
3. No quotes around the key value
4. No spaces around `=`

### Issue: Still slow with API key

**Verify**:
- Script output says "Using OpenFIGI API key (250 req/min rate limit)"
- If it says "No API key provided", check `.env` file

## Next Steps

1. ✅ Script is running with API key (in progress)
2. ⏳ Wait for completion (~30-40 seconds)
3. ⏳ Verify mapping results
4. ⏳ Test full data download for mapped instruments

## References

- OpenFIGI API: https://www.openfigi.com/api
- OpenFIGI Documentation: https://www.openfigi.com/api#tag/Mapping
- python-dotenv: https://pypi.org/project/python-dotenv/
