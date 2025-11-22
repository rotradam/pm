-- Add email column to profiles
alter table public.profiles 
add column if not exists email text;

-- Create a unique index on email for faster lookups
create unique index if not exists profiles_email_idx on public.profiles (email);

-- Update the handle_new_user function to include email
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, email)
  values (
    new.id, 
    new.raw_user_meta_data ->> 'full_name',
    new.email
  );
  return new;
end;
$$;

-- Backfill existing profiles with email from auth.users (requires superuser or service role, 
-- but we can try to do a best-effort update if running as a user with permissions, 
-- otherwise this part might need to be run manually or via a script with service role)
-- Note: In Supabase SQL Editor, you are usually a superuser or have sufficient privileges.
update public.profiles p
set email = u.email
from auth.users u
where p.id = u.id
and p.email is null;
