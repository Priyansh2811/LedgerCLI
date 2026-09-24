-- =========================================================
-- LedgerCLI Supabase / PostgreSQL Schema & Strict RLS Policies
-- =========================================================

-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Waitlist Table
create table if not exists public.waitlist (
    id uuid primary key default uuid_generate_v4(),
    email text unique not null,
    role text not null default 'developer',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Contact Inquiries Table
create table if not exists public.contacts (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    email text not null,
    message text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Site Analytics Table
create table if not exists public.site_analytics (
    id uuid primary key default uuid_generate_v4(),
    page_path text not null,
    referrer text,
    user_agent text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- =========================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================================

-- Enable RLS on all tables
alter table public.waitlist enable row level security;
alter table public.contacts enable row level security;
alter table public.site_analytics enable row level security;

-- Drop existing policies if re-running
drop policy if exists "Allow anonymous inserts into waitlist" on public.waitlist;
drop policy if exists "Deny all reads from waitlist" on public.waitlist;
drop policy if exists "Allow anonymous inserts into contacts" on public.contacts;
drop policy if exists "Deny all reads from contacts" on public.contacts;
drop policy if exists "Allow anonymous inserts into analytics" on public.site_analytics;
drop policy if exists "Deny all reads from analytics" on public.site_analytics;

-- Waitlist: Anyone can submit an email; no public reads allowed
create policy "Allow anonymous inserts into waitlist"
on public.waitlist for insert
to anon, authenticated
with check (true);

create policy "Deny all reads from waitlist"
on public.waitlist for select
to anon, authenticated
using (false);

-- Contacts: Anyone can submit messages; no public reads
create policy "Allow anonymous inserts into contacts"
on public.contacts for insert
to anon, authenticated
with check (true);

create policy "Deny all reads from contacts"
on public.contacts for select
to anon, authenticated
using (false);

-- Site Analytics: Anyone can push telemetry beacons; no public reads
create policy "Allow anonymous inserts into analytics"
on public.site_analytics for insert
to anon, authenticated
with check (true);

create policy "Deny all reads from analytics"
on public.site_analytics for select
to anon, authenticated
using (false);
