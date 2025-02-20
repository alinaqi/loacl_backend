-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS lacl_usage_metrics;
DROP TABLE IF EXISTS lacl_follow_up_suggestions;
DROP TABLE IF EXISTS lacl_guided_questions;
DROP TABLE IF EXISTS lacl_files;
DROP TABLE IF EXISTS lacl_messages;
DROP TABLE IF EXISTS lacl_threads;
DROP TABLE IF EXISTS lacl_sessions;
DROP TABLE IF EXISTS lacl_user_preferences;
DROP TABLE IF EXISTS lacl_assistants;

-- Create assistants table
CREATE TABLE lacl_assistants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    name TEXT,
    instructions TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    configuration JSONB DEFAULT '{}',
    tools_enabled TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_assistants_assistant_id ON lacl_assistants(assistant_id);

-- Create sessions table
CREATE TABLE lacl_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_type TEXT NOT NULL CHECK (session_type IN ('guest', 'authenticated')),
    assistant_id UUID REFERENCES lacl_assistants(id),
    user_id UUID,
    fingerprint TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired')),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_sessions_user_id ON lacl_sessions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_lacl_sessions_fingerprint ON lacl_sessions(fingerprint) WHERE fingerprint IS NOT NULL;
CREATE INDEX idx_lacl_sessions_expires_at ON lacl_sessions(expires_at) WHERE expires_at IS NOT NULL;

-- Create threads table
CREATE TABLE lacl_threads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES lacl_sessions(id) ON DELETE CASCADE,
    assistant_id UUID REFERENCES lacl_assistants(id),
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_threads_session_id ON lacl_threads(session_id);
CREATE INDEX idx_lacl_threads_updated_at ON lacl_threads(updated_at);
CREATE INDEX idx_lacl_threads_status ON lacl_threads(status);

-- Create messages table
CREATE TABLE lacl_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES lacl_threads(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,
    file_ids TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_messages_thread_id ON lacl_messages(thread_id);
CREATE INDEX idx_lacl_messages_created_at ON lacl_messages(created_at);
CREATE INDEX idx_lacl_messages_role ON lacl_messages(role);

-- Create files table
CREATE TABLE lacl_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES lacl_threads(id) ON DELETE CASCADE,
    message_id UUID REFERENCES lacl_messages(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_files_thread_id ON lacl_files(thread_id);
CREATE INDEX idx_lacl_files_message_id ON lacl_files(message_id);
CREATE INDEX idx_lacl_files_file_type ON lacl_files(file_type);

-- Create guided_questions table
CREATE TABLE lacl_guided_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id),
    question TEXT NOT NULL,
    category TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_guided_questions_assistant_id ON lacl_guided_questions(assistant_id);
CREATE INDEX idx_lacl_guided_questions_priority ON lacl_guided_questions(priority) WHERE is_active = true;

-- Create follow_up_suggestions table
CREATE TABLE lacl_follow_up_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thread_id UUID REFERENCES lacl_threads(id) ON DELETE CASCADE,
    message_id UUID REFERENCES lacl_messages(id),
    suggestion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    used_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_follow_up_suggestions_thread_id ON lacl_follow_up_suggestions(thread_id);
CREATE INDEX idx_lacl_follow_up_suggestions_message_id ON lacl_follow_up_suggestions(message_id);
CREATE INDEX idx_lacl_follow_up_suggestions_used ON lacl_follow_up_suggestions(used_at) WHERE used_at IS NULL;

-- Create usage_metrics table
CREATE TABLE lacl_usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id),
    session_id UUID REFERENCES lacl_sessions(id),
    thread_id UUID REFERENCES lacl_threads(id),
    metric_type TEXT NOT NULL,
    metric_value INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lacl_usage_metrics_assistant_id ON lacl_usage_metrics(assistant_id);
CREATE INDEX idx_lacl_usage_metrics_recorded_at ON lacl_usage_metrics(recorded_at);
CREATE INDEX idx_lacl_usage_metrics_type ON lacl_usage_metrics(metric_type);

-- Create user_preferences table
CREATE TABLE lacl_user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    theme TEXT DEFAULT 'light',
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    preferences JSONB DEFAULT '{}'
);

CREATE INDEX idx_lacl_user_preferences_user_id ON lacl_user_preferences(user_id);

-- Create helper functions
CREATE OR REPLACE FUNCTION lacl_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER lacl_update_assistants_updated_at
    BEFORE UPDATE ON lacl_assistants
    FOR EACH ROW
    EXECUTE FUNCTION lacl_update_updated_at();

CREATE TRIGGER lacl_update_threads_updated_at
    BEFORE UPDATE ON lacl_threads
    FOR EACH ROW
    EXECUTE FUNCTION lacl_update_updated_at();

-- Create session management function
CREATE OR REPLACE FUNCTION lacl_expire_guest_sessions()
RETURNS trigger AS $$
BEGIN
    UPDATE lacl_sessions
    SET status = 'expired'
    WHERE session_type = 'guest'
    AND expires_at < NOW()
    AND status != 'expired';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create session expiration trigger
CREATE TRIGGER lacl_expire_guest_sessions_trigger
    AFTER INSERT OR UPDATE ON lacl_sessions
    EXECUTE FUNCTION lacl_expire_guest_sessions();

-- Create usage tracking function
CREATE OR REPLACE FUNCTION lacl_track_message_tokens()
RETURNS trigger AS $$
BEGIN
    INSERT INTO lacl_usage_metrics (
        assistant_id,
        session_id,
        thread_id,
        metric_type,
        metric_value
    ) VALUES (
        (SELECT assistant_id FROM lacl_threads WHERE id = NEW.thread_id),
        (SELECT session_id FROM lacl_threads WHERE id = NEW.thread_id),
        NEW.thread_id,
        'tokens',
        NEW.tokens_used
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create message tokens tracking trigger
CREATE TRIGGER lacl_track_message_tokens_trigger
    AFTER INSERT ON lacl_messages
    FOR EACH ROW
    EXECUTE FUNCTION lacl_track_message_tokens();

-- Enable Row Level Security
ALTER TABLE lacl_assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_guided_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_follow_up_suggestions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_usage_metrics ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
CREATE POLICY "lacl_assistant_access_policy" ON lacl_assistants
    FOR ALL USING (
        auth.role() = 'authenticated' OR
        auth.role() = 'anon'
    );

CREATE POLICY "lacl_session_access_policy" ON lacl_sessions
    FOR ALL USING (
        (session_type = 'authenticated' AND user_id = auth.uid()) OR
        (session_type = 'guest' AND fingerprint = current_setting('request.headers')::json->>'fingerprint')
    );

CREATE POLICY "lacl_thread_access_policy" ON lacl_threads
    FOR ALL USING (
        session_id IN (
            SELECT id FROM lacl_sessions WHERE
                (session_type = 'authenticated' AND user_id = auth.uid()) OR
                (session_type = 'guest' AND fingerprint = current_setting('request.headers')::json->>'fingerprint')
        )
    );

CREATE POLICY "lacl_message_access_policy" ON lacl_messages
    FOR ALL USING (
        thread_id IN (
            SELECT id FROM lacl_threads WHERE session_id IN (
                SELECT id FROM lacl_sessions WHERE
                    (session_type = 'authenticated' AND user_id = auth.uid()) OR
                    (session_type = 'guest' AND fingerprint = current_setting('request.headers')::json->>'fingerprint')
            )
        )
    );

CREATE POLICY "lacl_file_access_policy" ON lacl_files
    FOR ALL USING (
        thread_id IN (
            SELECT id FROM lacl_threads WHERE session_id IN (
                SELECT id FROM lacl_sessions WHERE
                    (session_type = 'authenticated' AND user_id = auth.uid()) OR
                    (session_type = 'guest' AND fingerprint = current_setting('request.headers')::json->>'fingerprint')
            )
        )
    );

CREATE POLICY "lacl_guided_questions_access_policy" ON lacl_guided_questions
    FOR ALL USING (true);  -- Public read access

CREATE POLICY "lacl_follow_up_suggestions_access_policy" ON lacl_follow_up_suggestions
    FOR ALL USING (
        thread_id IN (
            SELECT id FROM lacl_threads WHERE session_id IN (
                SELECT id FROM lacl_sessions WHERE
                    (session_type = 'authenticated' AND user_id = auth.uid()) OR
                    (session_type = 'guest' AND fingerprint = current_setting('request.headers')::json->>'fingerprint')
            )
        )
    );

CREATE POLICY "lacl_usage_metrics_access_policy" ON lacl_usage_metrics
    FOR ALL USING (
        assistant_id IN (
            SELECT id FROM lacl_assistants WHERE TRUE  -- Restricted by assistant policy
        )
    );

-- Create function to clean up expired sessions
CREATE OR REPLACE FUNCTION lacl_cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM lacl_sessions
    WHERE status = 'expired'
    AND created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup job (requires pg_cron extension)
-- SELECT cron.schedule('0 0 * * *', 'SELECT lacl_cleanup_expired_sessions();');

-- Create trigger for updated_at
CREATE TRIGGER lacl_update_user_preferences_updated_at
    BEFORE UPDATE ON lacl_user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION lacl_update_updated_at();

-- Add RLS for user_preferences
ALTER TABLE lacl_user_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "lacl_user_preferences_access_policy" ON lacl_user_preferences
    FOR ALL USING (
        user_id = auth.uid()
    );
