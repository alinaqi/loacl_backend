-- Create users table (extending Supabase's auth.users)
create table if not exists public.users (
    id uuid references auth.users on delete cascade not null primary key,
    email text not null,
    is_active boolean default true,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone,
    constraint users_email_key unique (email)
);

-- Enable RLS
alter table public.users enable row level security;

-- Create users policies
create policy "Users can view their own data" on public.users
    for select using (auth.uid() = id);

create policy "Users can update their own data" on public.users
    for update using (auth.uid() = id);

-- Create assistants table
create table if not exists public.assistants (
    id uuid default gen_random_uuid() primary key,
    owner_id uuid references public.users on delete cascade not null,
    name text not null,
    description text,
    openai_assistant_id text not null,
    model text default 'gpt-4-turbo-preview',
    instructions text,
    tools jsonb default '[]'::jsonb,
    api_key text not null,
    is_active boolean default true,
    embed_settings jsonb default '{"theme": "light", "position": "bottom-right"}'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone,
    constraint assistants_owner_openai_key unique(owner_id, openai_assistant_id)
);

-- Enable RLS
alter table public.assistants enable row level security;

-- Create assistants policies
create policy "Users can view their own assistants" on public.assistants
    for select using (auth.uid() = owner_id);

create policy "Users can create their own assistants" on public.assistants
    for insert with check (auth.uid() = owner_id);

create policy "Users can update their own assistants" on public.assistants
    for update using (auth.uid() = owner_id);

create policy "Users can delete their own assistants" on public.assistants
    for delete using (auth.uid() = owner_id);

-- Create public access policy for active assistants
create policy "Public can view active assistants" on public.assistants
    for select using (is_active = true);

-- Create indexes
create index if not exists idx_assistants_owner_id on public.assistants(owner_id);
create index if not exists idx_assistants_openai_id on public.assistants(openai_assistant_id);
