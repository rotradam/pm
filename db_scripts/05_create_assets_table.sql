-- Create assets table
create table public.assets (
  id uuid default gen_random_uuid() primary key,
  ticker text not null unique,
  name text,
  category text, -- 'Crypto', 'Stock', etc.
  subcategory text,
  region text,
  currency text,
  exchange text, -- 'Binance', etc.
  logo_url text,
  price numeric,
  change_24h numeric,
  volume_24h numeric,
  sparkline_7d text, -- JSON string of prices
  last_updated timestamptz default now()
);

-- Enable RLS
alter table public.assets enable row level security;

-- Policies
create policy "Assets are viewable by everyone."
  on assets for select
  using ( true );

-- Only service role can insert/update (for ingestion scripts)
-- No policy needed for insert/update if we use service role key, 
-- but if we want to allow authenticated users to update (unlikely), we'd add one.
-- For now, read-only for users.
