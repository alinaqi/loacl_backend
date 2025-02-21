-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Helper Functions (needed for later)
CREATE OR REPLACE FUNCTION policy_exists(policy_name text, table_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = policy_name
        AND tablename = table_name
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION trigger_exists(trigger_name text, table_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_trigger
        WHERE tgname = trigger_name
        AND tgrelid = table_name::regclass
    );
END;
$$ LANGUAGE plpgsql;

-- Drop existing tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS lacl_analytics CASCADE;
DROP TABLE IF EXISTS lacl_usage_metrics CASCADE;
DROP TABLE IF EXISTS lacl_follow_up_suggestions CASCADE;
DROP TABLE IF EXISTS lacl_guided_questions CASCADE;
DROP TABLE IF EXISTS lacl_files CASCADE;
DROP TABLE IF EXISTS lacl_chat_messages CASCADE;
DROP TABLE IF EXISTS lacl_messages CASCADE;
DROP TABLE IF EXISTS lacl_chat_sessions CASCADE;
DROP TABLE IF EXISTS lacl_threads CASCADE;
DROP TABLE IF EXISTS lacl_sessions CASCADE;
DROP TABLE IF EXISTS lacl_user_preferences CASCADE;
DROP TABLE IF EXISTS lacl_assistants CASCADE;

-- 1. Create base tables first
CREATE TABLE IF NOT EXISTS lacl_assistants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    assistant_id TEXT NOT NULL,
    api_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    instructions TEXT,
    model TEXT DEFAULT 'gpt-4o-mini',
    tools_enabled TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    embed_settings JSONB DEFAULT '{"theme": "light", "position": "bottom-right"}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    features JSONB DEFAULT jsonb_build_object(
        'showFileUpload', true,
        'showVoiceInput', true,
        'showEmoji', true,
        'showGuidedQuestions', true,
        'showFollowUpSuggestions', true
    ),
    design_settings JSONB DEFAULT jsonb_build_object(
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
    )
);

CREATE TABLE IF NOT EXISTS lacl_chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS lacl_chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES lacl_chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tokens_used INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS lacl_usage_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id),
    session_id UUID REFERENCES lacl_chat_sessions(id),
    metric_type TEXT NOT NULL,
    metric_value INTEGER NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lacl_user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id) ON DELETE CASCADE,
    theme TEXT DEFAULT 'light',
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    preferences JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS lacl_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assistant_id UUID REFERENCES lacl_assistants(id) ON DELETE CASCADE,
    total_conversations INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    average_response_time FLOAT DEFAULT 0,
    user_satisfaction_rate FLOAT DEFAULT 0,
    daily_active_users INTEGER DEFAULT 0,
    messages_per_conversation FLOAT DEFAULT 0,
    peak_usage_times JSONB DEFAULT '[]',
    common_topics JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create indexes after tables
CREATE INDEX IF NOT EXISTS idx_lacl_assistants_assistant_id ON lacl_assistants(assistant_id);
CREATE INDEX IF NOT EXISTS idx_lacl_assistants_user_id ON lacl_assistants(user_id);
CREATE INDEX IF NOT EXISTS idx_lacl_chat_sessions_assistant_id ON lacl_chat_sessions(assistant_id);
CREATE INDEX IF NOT EXISTS idx_lacl_chat_sessions_fingerprint ON lacl_chat_sessions(fingerprint);
CREATE INDEX IF NOT EXISTS idx_lacl_chat_sessions_last_active ON lacl_chat_sessions(last_active_at);
CREATE INDEX IF NOT EXISTS idx_lacl_chat_messages_session_id ON lacl_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_lacl_chat_messages_created_at ON lacl_chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_lacl_usage_metrics_assistant_id ON lacl_usage_metrics(assistant_id);
CREATE INDEX IF NOT EXISTS idx_lacl_usage_metrics_recorded_at ON lacl_usage_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_lacl_usage_metrics_type ON lacl_usage_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_lacl_user_preferences_assistant_id ON lacl_user_preferences(assistant_id);
CREATE INDEX IF NOT EXISTS idx_lacl_analytics_assistant_id ON lacl_analytics(assistant_id);

-- 3. Create trigger functions
CREATE OR REPLACE FUNCTION lacl_update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION lacl_update_chat_session_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE lacl_chat_sessions
    SET last_active_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION lacl_track_message_tokens()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO lacl_usage_metrics (
        assistant_id,
        session_id,
        metric_type,
        metric_value
    ) VALUES (
        (SELECT assistant_id FROM lacl_chat_sessions WHERE id = NEW.session_id),
        NEW.session_id,
        'tokens',
        NEW.tokens_used
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION lacl_update_analytics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE lacl_analytics
    SET
        total_messages = total_messages + 1,
        messages_per_conversation = CAST(total_messages AS FLOAT) / NULLIF(total_conversations, 0),
        updated_at = NOW()
    WHERE assistant_id = (
        SELECT assistant_id
        FROM lacl_chat_sessions
        WHERE id = NEW.session_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create triggers
DO $$
BEGIN
    IF NOT trigger_exists('lacl_update_assistants_updated_at', 'lacl_assistants') THEN
        CREATE TRIGGER lacl_update_assistants_updated_at
            BEFORE UPDATE ON lacl_assistants
            FOR EACH ROW
            EXECUTE FUNCTION lacl_update_updated_at();
    END IF;

    IF NOT trigger_exists('lacl_update_chat_session_last_active_trigger', 'lacl_chat_messages') THEN
        CREATE TRIGGER lacl_update_chat_session_last_active_trigger
            AFTER INSERT ON lacl_chat_messages
            FOR EACH ROW
            EXECUTE FUNCTION lacl_update_chat_session_last_active();
    END IF;

    IF NOT trigger_exists('lacl_track_message_tokens_trigger', 'lacl_chat_messages') THEN
        CREATE TRIGGER lacl_track_message_tokens_trigger
            AFTER INSERT ON lacl_chat_messages
            FOR EACH ROW
            EXECUTE FUNCTION lacl_track_message_tokens();
    END IF;

    IF NOT trigger_exists('lacl_update_analytics_updated_at', 'lacl_analytics') THEN
        CREATE TRIGGER lacl_update_analytics_updated_at
            BEFORE UPDATE ON lacl_analytics
            FOR EACH ROW
            EXECUTE FUNCTION lacl_update_updated_at();
    END IF;

    IF NOT trigger_exists('lacl_update_analytics_trigger', 'lacl_chat_messages') THEN
        CREATE TRIGGER lacl_update_analytics_trigger
            AFTER INSERT ON lacl_chat_messages
            FOR EACH ROW
            EXECUTE FUNCTION lacl_update_analytics();
    END IF;
END;
$$;

-- 5. Enable RLS
ALTER TABLE lacl_assistants ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_usage_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE lacl_analytics ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS Policies
DO $$
BEGIN
    -- Assistants policies
    IF NOT policy_exists('Service role has full access', 'lacl_assistants') THEN
        CREATE POLICY "Service role has full access" ON lacl_assistants
            FOR ALL
            USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role')
            WITH CHECK (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');
    END IF;

    IF NOT policy_exists('Public can view active assistants', 'lacl_assistants') THEN
        CREATE POLICY "Public can view active assistants" ON lacl_assistants
            FOR SELECT USING (is_active = true);
    END IF;

    -- Chat sessions policies
    IF NOT policy_exists('Anyone can create chat sessions', 'lacl_chat_sessions') THEN
        CREATE POLICY "Anyone can create chat sessions" ON lacl_chat_sessions
            FOR INSERT WITH CHECK (
                assistant_id IN (SELECT id FROM lacl_assistants WHERE is_active = true)
            );
    END IF;

    IF NOT policy_exists('Users can view their chat sessions', 'lacl_chat_sessions') THEN
        CREATE POLICY "Users can view their chat sessions" ON lacl_chat_sessions
            FOR SELECT USING (fingerprint = current_setting('request.headers')::json->>'fingerprint');
    END IF;

    -- Chat messages policies
    IF NOT policy_exists('Anyone can create chat messages', 'lacl_chat_messages') THEN
        CREATE POLICY "Anyone can create chat messages" ON lacl_chat_messages
            FOR INSERT WITH CHECK (
                session_id IN (
                    SELECT id FROM lacl_chat_sessions
                    WHERE fingerprint = current_setting('request.headers')::json->>'fingerprint'
                )
            );
    END IF;

    IF NOT policy_exists('Users can view their chat messages', 'lacl_chat_messages') THEN
        CREATE POLICY "Users can view their chat messages" ON lacl_chat_messages
            FOR SELECT USING (
                session_id IN (
                    SELECT id FROM lacl_chat_sessions
                    WHERE fingerprint = current_setting('request.headers')::json->>'fingerprint'
                )
            );
    END IF;

    -- Analytics policy
    IF NOT policy_exists('Only assistant owners can view analytics', 'lacl_analytics') THEN
        CREATE POLICY "Only assistant owners can view analytics" ON lacl_analytics
            FOR ALL USING (
                assistant_id IN (
                    SELECT id FROM lacl_assistants
                    WHERE api_key = current_setting('request.headers')::json->>'x-api-key'
                )
            );
    END IF;
END;
$$;
