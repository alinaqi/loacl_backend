# LOACL Database Schema Design

## Overview
This document outlines the database schema for the LOACL (Lightweight OpenAI Assistants ChatBot Library) project. The schema is designed to work with Supabase (PostgreSQL) and supports both authenticated and guest users.

## Tables

### assistants
```sql
CREATE TABLE assistants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id TEXT NOT NULL,  -- OpenAI Assistant ID
    api_key TEXT NOT NULL,       -- Encrypted OpenAI API key
    name TEXT,
    instructions TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    configuration JSONB DEFAULT '{}',  -- Custom configuration
    tools_enabled TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_assistants_assistant_id ON assistants(assistant_id);
```

### sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_type TEXT NOT NULL CHECK (session_type IN ('guest', 'authenticated')),
    assistant_id UUID REFERENCES assistants(id),
    user_id UUID,  -- NULL for guest sessions
    fingerprint TEXT,  -- For guest session tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,  -- NULL for authenticated sessions
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_sessions_fingerprint ON sessions(fingerprint) WHERE fingerprint IS NOT NULL;
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at) WHERE expires_at IS NOT NULL;
```

### threads
```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    assistant_id UUID REFERENCES assistants(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_threads_session_id ON threads(session_id);
CREATE INDEX idx_threads_updated_at ON threads(updated_at);
```

### messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,  -- Track token usage
    file_ids TEXT[] DEFAULT '{}',   -- References to attached files
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### files
```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,  -- Path in Supabase storage
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_files_thread_id ON files(thread_id);
CREATE INDEX idx_files_message_id ON files(message_id);
```

### guided_questions
```sql
CREATE TABLE guided_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES assistants(id),
    question TEXT NOT NULL,
    category TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_guided_questions_assistant_id ON guided_questions(assistant_id);
```

### follow_up_suggestions
```sql
CREATE TABLE follow_up_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES threads(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id),
    suggestion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    used_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_follow_up_suggestions_thread_id ON follow_up_suggestions(thread_id);
CREATE INDEX idx_follow_up_suggestions_message_id ON follow_up_suggestions(message_id);
```

### usage_metrics
```sql
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES assistants(id),
    session_id UUID REFERENCES sessions(id),
    thread_id UUID REFERENCES threads(id),
    metric_type TEXT NOT NULL,  -- e.g., 'tokens', 'messages', 'files'
    metric_value INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_metrics_assistant_id ON usage_metrics(assistant_id);
CREATE INDEX idx_usage_metrics_recorded_at ON usage_metrics(recorded_at);
```

## Row Level Security (RLS) Policies

### Assistant Access
```sql
-- Only allow access to assistants they own
CREATE POLICY assistant_access_policy ON assistants
    USING (api_key = current_user_api_key());
```

### Session Access
```sql
-- Allow access to own authenticated sessions or guest sessions with matching fingerprint
CREATE POLICY session_access_policy ON sessions
    USING (
        (session_type = 'authenticated' AND user_id = auth.uid()) OR
        (session_type = 'guest' AND fingerprint = current_fingerprint())
    );
```

### Thread Access
```sql
-- Allow access to threads in their sessions
CREATE POLICY thread_access_policy ON threads
    USING (session_id IN (
        SELECT id FROM sessions WHERE 
            (session_type = 'authenticated' AND user_id = auth.uid()) OR
            (session_type = 'guest' AND fingerprint = current_fingerprint())
    ));
```

## Functions and Triggers

### Session Management
```sql
-- Automatically expire guest sessions
CREATE FUNCTION expire_guest_sessions() RETURNS trigger AS $$
BEGIN
    UPDATE sessions
    SET status = 'expired'
    WHERE session_type = 'guest'
    AND expires_at < NOW();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER expire_guest_sessions_trigger
    AFTER INSERT OR UPDATE ON sessions
    EXECUTE FUNCTION expire_guest_sessions();
```

### Usage Tracking
```sql
-- Automatically track message tokens
CREATE FUNCTION track_message_tokens() RETURNS trigger AS $$
BEGIN
    INSERT INTO usage_metrics (
        assistant_id,
        session_id,
        thread_id,
        metric_type,
        metric_value
    ) VALUES (
        NEW.assistant_id,
        NEW.session_id,
        NEW.thread_id,
        'tokens',
        NEW.tokens_used
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_message_tokens_trigger
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION track_message_tokens();
```

## Indexes and Performance Considerations

1. **Composite Indexes**
   - For frequently accessed combinations
   - For sorting and filtering operations

2. **JSONB Indexes**
   - For frequently queried JSONB fields
   - For specific metadata patterns

3. **Partial Indexes**
   - For specific status values
   - For active/inactive records

## Backup and Recovery

1. **Continuous Backup**
   - Enabled by default in Supabase
   - Point-in-time recovery available

2. **Retention Policy**
   - Keep backups for 30 days
   - Daily snapshots

## Security Considerations

1. **Encryption**
   - API keys stored encrypted
   - Sensitive data in metadata encrypted

2. **Access Control**
   - Row Level Security (RLS) enabled
   - Role-based access control

3. **Data Sanitization**
   - Input validation at database level
   - Output sanitization for sensitive fields 