-- Create chat sessions table
create table if not exists public.chat_sessions (
    id uuid default gen_random_uuid() primary key,
    assistant_id uuid references public.assistants(id) on delete cascade not null,
    fingerprint text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    last_active_at timestamp with time zone default timezone('utc'::text, now()) not null,
    metadata jsonb default '{}'
);

-- Create chat messages table
create table if not exists public.chat_messages (
    id uuid default gen_random_uuid() primary key,
    session_id uuid references public.chat_sessions(id) on delete cascade not null,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    tokens_used integer default 0,
    metadata jsonb default '{}'
);

-- Enable RLS
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;

-- Create indexes
create index if not exists idx_chat_sessions_assistant_id on public.chat_sessions(assistant_id);
create index if not exists idx_chat_sessions_fingerprint on public.chat_sessions(fingerprint);
create index if not exists idx_chat_sessions_last_active on public.chat_sessions(last_active_at);
create index if not exists idx_chat_messages_session_id on public.chat_messages(session_id);
create index if not exists idx_chat_messages_created_at on public.chat_messages(created_at);

-- Create policies for anonymous access
create policy "Anyone can create chat sessions" on public.chat_sessions
    for insert with check (
        assistant_id in (select id from public.assistants where is_active = true)
    );

create policy "Users can view their chat sessions" on public.chat_sessions
    for select using (fingerprint = current_setting('request.headers')::json->>'fingerprint');

create policy "Anyone can create chat messages" on public.chat_messages
    for insert with check (
        session_id in (
            select id from public.chat_sessions
            where fingerprint = current_setting('request.headers')::json->>'fingerprint'
        )
    );

create policy "Users can view their chat messages" on public.chat_messages
    for select using (
        session_id in (
            select id from public.chat_sessions
            where fingerprint = current_setting('request.headers')::json->>'fingerprint'
        )
    );

-- Create function to update last_active_at
create or replace function update_chat_session_last_active()
returns trigger as $$
begin
    update public.chat_sessions
    set last_active_at = now()
    where id = new.session_id;
    return new;
end;
$$ language plpgsql;

-- Create trigger to update last_active_at
create trigger update_chat_session_last_active_trigger
    after insert on public.chat_messages
    for each row
    execute function update_chat_session_last_active();
