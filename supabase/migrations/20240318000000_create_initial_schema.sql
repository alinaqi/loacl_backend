-- Helper function for policy checks
create or replace function policy_exists(policy_name text, table_name text)
returns boolean as $$
begin
    return exists (
        select 1 from pg_policies
        where policyname = policy_name
        and tablename = table_name
    );
end;
$$ language plpgsql;

-- Drop existing foreign key if exists
alter table if exists lacl_assistants
    drop constraint if exists lacl_assistants_user_id_fkey;

-- Create assistants table
create table if not exists lacl_assistants (
    id uuid default gen_random_uuid() primary key,
    user_id uuid not null,
    name text not null,
    description text,
    assistant_id text not null,
    model text default 'gpt-4-turbo-preview',
    instructions text,
    tools_enabled text[] default '{}',
    api_key text not null,
    is_active boolean default true,
    embed_settings jsonb default '{"theme": "light", "position": "bottom-right"}'::jsonb,
    features jsonb default jsonb_build_object(
        'showFileUpload', true,
        'showVoiceInput', true,
        'showEmoji', true,
        'showGuidedQuestions', true,
        'showFollowUpSuggestions', true
    ),
    design_settings jsonb default jsonb_build_object(
        'theme', jsonb_build_object(
            'primary_color', '#4F46E5',
            'secondary_color', '#6366F1',
            'text_color', '#111827',
            'background_color', '#FFFFFF'
        ),
        'layout', jsonb_build_object(
            'width', '380px',
            'height', '600px',
            'position', 'right',
            'bubble_icon', null
        ),
        'typography', jsonb_build_object(
            'font_family', 'Inter, system-ui, sans-serif',
            'font_size', '14px'
        )
    ),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    updated_at timestamp with time zone,
    metadata jsonb default '{}'::jsonb,
    constraint assistants_user_openai_key unique(user_id, assistant_id)
);

-- Enable RLS
alter table lacl_assistants enable row level security;

-- Create assistants policies
do $$
begin
    if not policy_exists('Users can view their own assistants', 'lacl_assistants') then
        create policy "Users can view their own assistants" on lacl_assistants
            for select using (auth.uid() = user_id);
    end if;

    if not policy_exists('Users can create their own assistants', 'lacl_assistants') then
        create policy "Users can create their own assistants" on lacl_assistants
            for insert with check (auth.uid() = user_id);
    end if;

    if not policy_exists('Users can update their own assistants', 'lacl_assistants') then
        create policy "Users can update their own assistants" on lacl_assistants
            for update using (auth.uid() = user_id);
    end if;

    if not policy_exists('Users can delete their own assistants', 'lacl_assistants') then
        create policy "Users can delete their own assistants" on lacl_assistants
            for delete using (auth.uid() = user_id);
    end if;

    if not policy_exists('Public can view active assistants', 'lacl_assistants') then
        create policy "Public can view active assistants" on lacl_assistants
            for select using (is_active = true);
    end if;
end;
$$;

-- Create indexes
create index if not exists idx_assistants_user_id on lacl_assistants(user_id);
create index if not exists idx_assistants_openai_id on lacl_assistants(assistant_id);

-- Create API keys table
create table if not exists lacl_api_keys (
    id uuid default gen_random_uuid() primary key,
    user_id uuid not null,
    name text not null,
    key text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    is_active boolean default true,
    constraint api_keys_user_name unique(user_id, name)
);

-- Enable RLS on API keys table
alter table lacl_api_keys enable row level security;

-- Create API keys policies
do $$
begin
    -- Users can view their own API keys
    if not policy_exists('Users can view their own API keys', 'lacl_api_keys') then
        create policy "Users can view their own API keys" on lacl_api_keys
            for select using (auth.uid()::uuid = user_id);
    end if;

    -- Users can create their own API keys
    if not policy_exists('Users can create their own API keys', 'lacl_api_keys') then
        create policy "Users can create their own API keys" on lacl_api_keys
            for insert with check (auth.uid()::uuid = user_id);
    end if;

    -- Users can update their own API keys
    if not policy_exists('Users can update their own API keys', 'lacl_api_keys') then
        create policy "Users can update their own API keys" on lacl_api_keys
            for update using (auth.uid()::uuid = user_id);
    end if;

    -- Users can delete their own API keys
    if not policy_exists('Users can delete their own API keys', 'lacl_api_keys') then
        create policy "Users can delete their own API keys" on lacl_api_keys
            for delete using (auth.uid()::uuid = user_id);
    end if;
end;
$$;

-- Create indexes for API keys
create index if not exists idx_api_keys_user_id on lacl_api_keys(user_id);
create index if not exists idx_api_keys_key on lacl_api_keys(key);
