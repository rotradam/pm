-- Create profiles table
create table public.profiles (
  id uuid references auth.users not null primary key,
  full_name text,
  tier text default 'free',
  created_at timestamptz default now()
);

-- Create portfolios table
create table public.portfolios (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) not null,
  name text not null,
  description text,
  created_at timestamptz default now()
);

-- Create portfolio_assets table
create table public.portfolio_assets (
  id uuid default gen_random_uuid() primary key,
  portfolio_id uuid references public.portfolios(id) on delete cascade not null,
  asset_symbol text not null,
  asset_type text not null,
  source text not null,
  quantity numeric,
  allocation_target numeric,
  created_at timestamptz default now()
);

-- Enable RLS
alter table public.profiles enable row level security;
alter table public.portfolios enable row level security;
alter table public.portfolio_assets enable row level security;

-- Policies
create policy "Public profiles are viewable by everyone."
  on profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile."
  on profiles for update
  using ( auth.uid() = id );

create policy "Users can view own portfolios."
  on portfolios for select
  using ( auth.uid() = user_id );

create policy "Users can insert own portfolios."
  on portfolios for insert
  with check ( auth.uid() = user_id );

create policy "Users can update own portfolios."
  on portfolios for update
  using ( auth.uid() = user_id );

create policy "Users can delete own portfolios."
  on portfolios for delete
  using ( auth.uid() = user_id );

create policy "Users can view own portfolio assets."
  on portfolio_assets for select
  using ( exists ( select 1 from portfolios where id = portfolio_assets.portfolio_id and user_id = auth.uid() ) );

create policy "Users can insert own portfolio assets."
  on portfolio_assets for insert
  with check ( exists ( select 1 from portfolios where id = portfolio_assets.portfolio_id and user_id = auth.uid() ) );

-- Trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, new.raw_user_meta_data ->> 'full_name');
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
