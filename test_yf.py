import yfinance as yf

ticker = "HYPE-USD"
print(f"Testing {ticker}...")
data = yf.download(ticker, period="1y")
print(data)

if data.empty:
    print(f"{ticker}: No data found.")
else:
    print(f"{ticker}: Data found ({len(data)} rows).")
