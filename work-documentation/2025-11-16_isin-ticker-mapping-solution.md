# ISIN to Ticker Mapping Solution

**Date**: 2025-11-16  
**Component**: Data pipeline - ISIN resolution  
**Status**: Working solution implemented

## Problem

The initial approach tried to use ISINs directly as Yahoo Finance tickers (e.g., `IE00B4L5Y983.L`), but **Yahoo Finance uses actual trading tickers, not ISINs**.

### Error
```
download() got an unexpected keyword argument 'show_errors'
YFTzMissingError('possibly delisted; no timezone found')
```

## Root Cause

1. **yfinance API change**: The `show_errors` parameter was removed in recent versions
2. **Wrong ticker format**: ISINs aren't valid Yahoo Finance tickers

Example:
- ❌ Wrong: `IE00B4L5Y983.L` (ISIN + exchange suffix)
- ✅ Correct: `IWDA.L` (actual LSE ticker for iShares Core MSCI World)

## Solution

### 1. Created Verified Mapping File

**File**: `data/isin_ticker_mapping_verified.json`

```json
{
  "IE00B4L5Y983": "IWDA.L",
  "IE00BJ0KDQ92": "XDWD.L",
  "IE00BK5BQT80": "VWRL.L",
  "IE00B44Z5B48": "SPYY.L",
  "FR0010315770": "CW8.PA"
}
```

### 2. Updated IsinMapper

**Changes to** `backend/data/mapper.py`:
- Now loads verified mappings from JSON file
- Returns `None` for unmapped ISINs (instead of guessing)
- Logs clear warnings with instructions for adding new mappings
- Reports mapping success rate

### 3. Created ISIN Resolver Helper

**New file**: `backend/data/isin_resolver.py`

Provides:
- Template for verified mappings
- Ticker validation function
- Instructions for manual research

### 4. Fixed yfinance API Issues

**Changes to** `backend/data/prices.py`:
- Removed `show_errors` parameter (not supported in yfinance 0.2.66)
- Added handling for multi-level columns
- Better fallback from Adj Close to Close

## How to Add More Mappings

### Method 1: Manual Research (Recommended)

1. Go to https://finance.yahoo.com/
2. Search by ISIN or ETF name
3. Copy the ticker symbol from the URL
4. Add to `data/isin_ticker_mapping_verified.json`:

```json
{
  "YOUR_ISIN": "TICKER.EXCHANGE"
}
```

### Method 2: Use OpenFIGI API (For bulk mapping)

```python
import requests

def get_ticker_from_openfigi(isin):
    url = "https://api.openfigi.com/v3/mapping"
    headers = {"Content-Type": "application/json"}
    payload = [{"idType": "ID_ISIN", "idValue": isin}]
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data and "data" in data[0]:
            for item in data[0]["data"]:
                if "ticker" in item:
                    return item["ticker"]
    return None
```

### Method 3: Check Common Patterns

For European ETFs, common ticker patterns:
- iShares: `ISH[...].[EXCHANGE]` or short codes like `IWDA.L`
- Vanguard: `V[...].[EXCHANGE]` like `VWRL.L`
- Xtrackers: `XTR[...].[EXCHANGE]` or `X[...].L`

Exchanges:
- `.L` = London Stock Exchange
- `.DE` = Xetra (Frankfurt)
- `.PA` = Euronext Paris
- `.AS` = Euronext Amsterdam
- `.SW` = SIX Swiss Exchange

## Current Status

### Working ✅
- 5/5 Global Equity ETFs mapped and downloaded
- 2565 days of data (2015-11-19 to 2025-11-14)
- Price matrix saved to `data/processed/prices_*.parquet`

### TODO ⏳
- Map remaining 95 ISINs from universe
- Test with more sectors
- Consider automating with OpenFIGI API

## Files Changed

1. `backend/data/mapper.py` - Updated to use verified mappings
2. `backend/data/prices.py` - Fixed yfinance API compatibility
3. `backend/data/isin_resolver.py` - New helper tool
4. `scripts/download_data.py` - Filter unmapped ISINs before download
5. `data/isin_ticker_mapping_verified.json` - New verified mappings file

## Testing

```bash
# Activate environment
source activate_olps.sh

# Test with Global Equity sector (5 ETFs)
python scripts/download_data.py --sectors "Global Equity"

# Expected output:
# ✓ Success! Price matrix saved to: data/processed/prices_*.parquet
#   Shape: 2565 days × 5 assets
```

## Next Steps

1. **Map more ISINs**: Add verified mappings for all 100 instruments
2. **Consider automation**: Use OpenFIGI API or similar service
3. **Add validation**: Test all mapped tickers work
4. **Document mappings**: Add comments in JSON with ETF names

## References

- Yahoo Finance: https://finance.yahoo.com/
- OpenFIGI API: https://www.openfigi.com/api
- yfinance docs: https://github.com/ranaroussi/yfinance
