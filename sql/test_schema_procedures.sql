-- Create a function to set up the test schema
create or replace function create_test_schema()
returns void
language plpgsql
security definer
as $$
begin
    -- Create test schema if it doesn't exist
    if not exists (select 1 from information_schema.schemata where schema_name = 'test') then
        execute 'create schema test';
    end if;

    -- Clean existing data
    execute 'truncate table test.loacl_conversations cascade';
    execute 'truncate table test.loacl_messages cascade';
    execute 'truncate table test.loacl_files cascade';
    execute 'truncate table test.loacl_user_preferences cascade';
    execute 'truncate table test.loacl_assistants cascade';
    execute 'truncate table test.loacl_assistant_files cascade';
    execute 'truncate table test.loacl_threads cascade';
    execute 'truncate table test.loacl_thread_messages cascade';
    execute 'truncate table test.loacl_thread_files cascade';

    -- Reset sequences
    execute 'alter sequence test.loacl_conversations_id_seq restart with 1';
    execute 'alter sequence test.loacl_messages_id_seq restart with 1';
    execute 'alter sequence test.loacl_files_id_seq restart with 1';
    execute 'alter sequence test.loacl_user_preferences_id_seq restart with 1';
    execute 'alter sequence test.loacl_assistants_id_seq restart with 1';
    execute 'alter sequence test.loacl_assistant_files_id_seq restart with 1';
    execute 'alter sequence test.loacl_threads_id_seq restart with 1';
    execute 'alter sequence test.loacl_thread_messages_id_seq restart with 1';
    execute 'alter sequence test.loacl_thread_files_id_seq restart with 1';
end;
$$;

-- Create a function to clean up the test schema
create or replace function cleanup_test_schema()
returns void
language plpgsql
security definer
as $$
begin
    -- Clean all test data
    execute 'truncate table test.loacl_conversations cascade';
    execute 'truncate table test.loacl_messages cascade';
    execute 'truncate table test.loacl_files cascade';
    execute 'truncate table test.loacl_user_preferences cascade';
    execute 'truncate table test.loacl_assistants cascade';
    execute 'truncate table test.loacl_assistant_files cascade';
    execute 'truncate table test.loacl_threads cascade';
    execute 'truncate table test.loacl_thread_messages cascade';
    execute 'truncate table test.loacl_thread_files cascade';
end;
$$;

-- Create a function to verify test schema tables exist
create or replace function verify_test_schema()
returns boolean
language plpgsql
security definer
as $$
begin
    return exists (
        select 1
        from information_schema.tables
        where table_schema = 'test'
        and table_name in (
            'loacl_conversations',
            'loacl_messages',
            'loacl_files',
            'loacl_user_preferences',
            'loacl_assistants',
            'loacl_assistant_files',
            'loacl_threads',
            'loacl_thread_messages',
            'loacl_thread_files'
        )
    );
end;
$$;
