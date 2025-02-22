-- Create chat sessions table
create table if not exists lacl_chat_sessions (
    id uuid default gen_random_uuid() primary key,
    assistant_id uuid references lacl_assistants(id) on delete cascade not null,
    fingerprint text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    last_active_at timestamp with time zone default timezone('utc'::text, now()) not null,
    metadata jsonb default '{}'::jsonb
);

-- Enable RLS
alter table lacl_chat_sessions enable row level security;

-- Create chat messages table
create table if not exists lacl_chat_messages (
    id uuid default gen_random_uuid() primary key,
    session_id uuid references lacl_chat_sessions(id) on delete cascade not null,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    tokens_used integer default 0,
    metadata jsonb default '{}'::jsonb
);

-- Enable RLS
alter table lacl_chat_messages enable row level security;

-- Create policies for chat sessions and messages
do $$
begin
    -- Chat sessions policies
    if not policy_exists('Users can view sessions for their assistants', 'lacl_chat_sessions') then
        create policy "Users can view sessions for their assistants" on lacl_chat_sessions
            for select using (
                assistant_id in (select id from lacl_assistants where user_id = auth.uid())
            );
    end if;

    if not policy_exists('Users can create sessions for their assistants', 'lacl_chat_sessions') then
        create policy "Users can create sessions for their assistants" on lacl_chat_sessions
            for insert with check (
                assistant_id in (select id from lacl_assistants where user_id = auth.uid())
            );
    end if;

    if not policy_exists('Users can update sessions for their assistants', 'lacl_chat_sessions') then
        create policy "Users can update sessions for their assistants" on lacl_chat_sessions
            for update using (
                assistant_id in (select id from lacl_assistants where user_id = auth.uid())
            );
    end if;

    if not policy_exists('Users can delete sessions for their assistants', 'lacl_chat_sessions') then
        create policy "Users can delete sessions for their assistants" on lacl_chat_sessions
            for delete using (
                assistant_id in (select id from lacl_assistants where user_id = auth.uid())
            );
    end if;

    -- Chat messages policies
    if not policy_exists('Users can view messages for their sessions', 'lacl_chat_messages') then
        create policy "Users can view messages for their sessions" on lacl_chat_messages
            for select using (
                session_id in (
                    select id from lacl_chat_sessions where
                    assistant_id in (select id from lacl_assistants where user_id = auth.uid())
                )
            );
    end if;

    if not policy_exists('Users can create messages for their sessions', 'lacl_chat_messages') then
        create policy "Users can create messages for their sessions" on lacl_chat_messages
            for insert with check (
                session_id in (
                    select id from lacl_chat_sessions where
                    assistant_id in (select id from lacl_assistants where user_id = auth.uid())
                )
            );
    end if;

    if not policy_exists('Users can update messages for their sessions', 'lacl_chat_messages') then
        create policy "Users can update messages for their sessions" on lacl_chat_messages
            for update using (
                session_id in (
                    select id from lacl_chat_sessions where
                    assistant_id in (select id from lacl_assistants where user_id = auth.uid())
                )
            );
    end if;

    if not policy_exists('Users can delete messages for their sessions', 'lacl_chat_messages') then
        create policy "Users can delete messages for their sessions" on lacl_chat_messages
            for delete using (
                session_id in (
                    select id from lacl_chat_sessions where
                    assistant_id in (select id from lacl_assistants where user_id = auth.uid())
                )
            );
    end if;
end;
$$;

-- Create indexes
create index if not exists idx_chat_sessions_assistant_id on lacl_chat_sessions(assistant_id);
create index if not exists idx_chat_messages_session_id on lacl_chat_messages(session_id);

-- Create function to update last_active_at
create or replace function update_chat_session_last_active()
returns trigger as $$
begin
    update lacl_chat_sessions
    set last_active_at = now()
    where id = new.session_id;
    return new;
end;
$$ language plpgsql;

-- Create trigger to update last_active_at
drop trigger if exists update_chat_session_last_active_trigger on lacl_chat_messages;
create trigger update_chat_session_last_active_trigger
    after insert on lacl_chat_messages
    for each row
    execute function update_chat_session_last_active();
