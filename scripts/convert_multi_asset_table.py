"""
Convert multi_asset_table.md to etf_universe_full_clean.csv format.
"""
import pandas as pd
import re

# Read the markdown table
with open('documents/multi_asset_table.md', 'r') as f:
    content = f.read()

# Extract table rows (skip header and separator)
lines = content.strip().split('\n')
data_lines = [line for line in lines[2:] if line.strip().startswith('|')]

# Parse each row
records = []
for line in data_lines:
    # Split by | and clean
    parts = [p.strip() for p in line.split('|')[1:-1]]  # Skip first and last empty
    
    if len(parts) >= 8:
        isin = parts[0]
        wkn = parts[1]
        name = parts[2].replace('**', '')  # Remove markdown bold
        sector = parts[3]
        role = parts[4]
        domicile = parts[5]
        currency = parts[6]
        acc_dist = parts[7]
        notes = parts[8] if len(parts) > 8 else ''
        
        records.append({
            'isin': isin,
            'wkn': wkn,
            'name': name,
            'sector': sector,
            'role': role,
            'domicile': domicile,
            'currency': currency,
            'accumulating_distributing': acc_dist,
            'notes': notes
        })

# Create DataFrame
df = pd.DataFrame(records)

# Save to CSV
output_path = 'documents/etf_universe_full_clean.csv'
df.to_csv(output_path, index=False)

print(f"✓ Converted {len(df)} securities")
print(f"✓ Saved to: {output_path}")
print(f"\nBreakdown by role:")
print(df['role'].value_counts())
print(f"\nBreakdown by sector:")
print(df['sector'].value_counts().head(10))
