-- Add preferred_exchanges to profiles
alter table public.profiles 
add column if not exists preferred_exchanges text[] default '{}';

-- Create subscriptions table
create table public.subscriptions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) not null,
  status text not null default 'inactive',
  plan_id text,
  current_period_end timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Enable RLS for subscriptions
alter table public.subscriptions enable row level security;

-- Policies for subscriptions
create policy "Users can view own subscription."
  on subscriptions for select
  using ( auth.uid() = user_id );
