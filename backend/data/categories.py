"""
Predefined asset categories and their corresponding tickers.
"""

CATEGORIES = {
    "US Equity Indexes": [
        "^GSPC",  # S&P 500
        "^DJI",   # Dow Jones Industrial Average
        "^IXIC",  # NASDAQ Composite
        "^RUT",   # Russell 2000
    ],
    "US Equity Sectors": [
        "XLC", # Communication Services
        "XLY", # Consumer Discretionary
        "XLP", # Consumer Staples
        "XLE", # Energy
        "XLF", # Financials
        "XLV", # Health Care
        "XLI", # Industrials
        "XLB", # Materials
        "XLRE", # Real Estate
        "XLK", # Technology
        "XLU", # Utilities
    ],
    "S&P500 Singles (Top 10)": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ"
    ],
    "World Ex-USA Indexes": [
        "VXUS", # Vanguard Total International Stock
        "ACWX", # iShares MSCI ACWI ex U.S.
    ],
    "Developed Countries": [
        "EFA", # iShares MSCI EAFE
        "VEA", # Vanguard FTSE Developed Markets
        "EWJ", # Japan
        "EWG", # Germany
        "EWU", # UK
    ],
    "Emerging Markets": [
        "EEM", # iShares MSCI Emerging Markets
        "VWO", # Vanguard FTSE Emerging Markets
        "MCHI", # China
        "INDA", # India
        "EWZ", # Brazil
    ],
    "US Treasuries": [
        "SHY", # 1-3 Year
        "IEF", # 7-10 Year
        "TLT", # 20+ Year
        "GOVT", # All maturities
    ],
    "US TIPS": [
        "TIP", # iShares TIPS Bond
        "VTIP", # Vanguard Short-Term Inflation-Protected Securities
    ],
    "US Corporate Credit": [
        "LQD", # Investment Grade
        "HYG", # High Yield
        "JNK", # High Yield
    ],
    "International Fixed Income": [
        "BNDX", # Vanguard Total International Bond
        "IGOV", # iShares International Treasury Bond
    ],
    "Commodities Index": [
        "DBC", # Invesco DB Commodity Index Tracking
        "GSG", # iShares S&P GSCI Commodity-Indexed Trust
    ],
    "Energy": [
        "XLE", # Energy Select Sector SPDR
        "VDE", # Vanguard Energy
        "USO", # United States Oil
        "UNG", # United States Natural Gas
    ],
    "Precious Metals": [
        "GLD", # Gold
        "IAU", # Gold
        "SLV", # Silver
        "PPLT", # Platinum
    ],
    "Soft Commodities": [
        "DBA", # Agriculture
        "CORN", # Corn
        "SOYB", # Soybean
        "WEAT", # Wheat
    ],
    "Shipping": [
        "BDRY", # Breakwave Dry Bulk Shipping
    ],
    "Real Estate": [
        "VNQ", # Vanguard Real Estate
        "REM", # iShares Mortgage Real Estate
        "IYR", # iShares U.S. Real Estate
    ],
    "US Dollar": [
        "UUP", # Invesco DB US Dollar Index Bullish
    ],
    "Major FX Pairs": [
        "EURUSD=X",
        "JPY=X",
        "GBPUSD=X",
        "AUDUSD=X",
        "CAD=X",
        "CHF=X",
    ],
    "Boomercoin": [
        "BTC-USD",
        "ETH-USD",
        "LTC-USD",
        "BCH-USD",
    ],
    "Shitcoins": [
        "DOGE-USD",
        "SHIB-USD",
        "PEPE-USD",
        "FLOKI-USD",
        "BONK-USD",
        "WIF-USD",
    ]
}

def get_all_tickers():
    """Return a flat list of all unique tickers across all categories."""
    tickers = set()
    for category_tickers in CATEGORIES.values():
        tickers.update(category_tickers)
    return sorted(list(tickers))
