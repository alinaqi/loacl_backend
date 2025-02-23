# Frontend API Guide

This document outlines all the available API endpoints for the LOACL frontend application.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

There are two ways to authenticate with the API:

1. Using Bearer Token (for frontend applications)
2. Using API Key (for external integrations)

### Bearer Token Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

Response: {
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

#### Login
```http
POST /auth/login/access-token
Content-Type: application/x-www-form-urlencoded

grant_type=password&
username=user@example.com&
password=secure_password

Response: {
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Use the Bearer token in the Authorization header:
```
Authorization: Bearer eyJ...
```

### API Key Authentication

For external integrations, you can use an API key instead of Bearer token authentication. Add your API key to the `X-API-Key` header:

```
X-API-Key: loacl_your_api_key
```

Example using curl:
```bash
curl "http://localhost:8000/api/v1/api-keys" \
  -H "X-API-Key: loacl_your_api_key"
```

## API Keys

### Create API Key
```http
POST /api-keys
Content-Type: application/json

{
  "name": "My API Key"
}

Response: {
  "id": "uuid",
  "name": "My API Key",
  "key": "loacl_...",
  "created_at": "2024-02-22T12:00:00Z"
}
```

### List API Keys
```http
GET /api-keys

Response: [
  {
    "id": "uuid",
    "name": "My API Key",
    "key": "loacl_...",
    "created_at": "2024-02-22T12:00:00Z"
  }
]
```

### Get API Key
```http
GET /api-keys/{api_key_id}

Response: {
  "id": "uuid",
  "name": "My API Key",
  "key": "loacl_...",
  "created_at": "2024-02-22T12:00:00Z"
}
```

### Update API Key
```http
PATCH /api-keys/{api_key_id}
Content-Type: application/json

{
  "name": "Updated API Key Name"
}

Response: {
  "id": "uuid",
  "name": "Updated API Key Name",
  "key": "loacl_...",
  "created_at": "2024-02-22T12:00:00Z"
}
```

### Delete API Key
```http
DELETE /api-keys/{api_key_id}

Response: 204 No Content
```

## Assistants

### Create Assistant
```http
POST /assistants
Content-Type: application/json

{
  "name": "Test Assistant",
  "description": "A helpful assistant",
  "instructions": "You are a helpful assistant",
  "model": "gpt-4-turbo-preview",
  "api_key": "sk-...",
  "assistant_id": "asst_...",
  "tools_enabled": ["code_interpreter"],
  "design_settings": {
    "theme": {
      "primary_color": "#4F46E5",
      "secondary_color": "#6366F1",
      "text_color": "#111827",
      "background_color": "#FFFFFF"
    },
    "layout": {
      "width": "380px",
      "height": "600px",
      "position": "right",
      "bubble_icon": null
    },
    "typography": {
      "font_family": "Inter, system-ui, sans-serif",
      "font_size": "14px"
    }
  },
  "features": {
    "showFileUpload": true,
    "showVoiceInput": true,
    "showEmoji": true,
    "showGuidedQuestions": true,
    "showFollowUpSuggestions": true
  },
  "is_active": true
}

Response: {
  "id": "uuid",
  "name": "Test Assistant",
  "description": "A helpful assistant",
  ...
}
```

### List Assistants
```http
GET /assistants

Response: [
  {
    "id": "uuid",
    "name": "Test Assistant",
    "description": "A helpful assistant",
    ...
  }
]
```

### Get Assistant
```http
GET /assistants/{assistant_id}

Response: {
  "id": "uuid",
  "name": "Test Assistant",
  "description": "A helpful assistant",
  ...
}
```

### Update Assistant
```http
PUT /assistants/{assistant_id}
Content-Type: application/json

{
  "name": "Updated Assistant",
  "description": "Updated description",
  "instructions": "Updated instructions",
  "model": "gpt-4-turbo-preview",
  "api_key": "sk-...",
  "tools_enabled": ["code_interpreter"],
  "design_settings": {...},
  "features": {...},
  "is_active": true
}

Response: {
  "id": "uuid",
  "name": "Updated Assistant",
  ...
}
```

### Delete Assistant
```http
DELETE /assistants/{assistant_id}

Response: 204 No Content
```

### Get Assistant Analytics
```http
GET /assistants/{assistant_id}/analytics

Response: {
  "total_conversations": 100,
  "total_messages": 500,
  "average_response_time": 2.5,
  "user_satisfaction_rate": 4.8,
  "most_common_topics": ["topic1", "topic2"]
}
```

### Validate Assistant Credentials
```http
POST /assistants/{assistant_id}/validate

Response: {
  "is_valid": true
}
```

### Get Embed Code
```http
GET /assistants/{assistant_id}/embed

Response: {
  "code": "<script>...</script>"
}
```

### Update Embed Settings
```http
PUT /assistants/{assistant_id}/embed
Content-Type: application/json

{
  "allowed_domains": ["example.com"],
  "custom_styles": "/* CSS */",
  "custom_script": "// JS",
  "position": "right",
  "auto_open": false,
  "delay_open": 3000
}

Response: {
  "id": "uuid",
  "name": "Assistant Name",
  ...
}
```

## Assistant Communication

### Create Thread
```http
POST /assistant-communication/threads?assistant_id={assistant_id}
Content-Type: application/json

{
  "messages": [
    {
      "content": "Hello!",
      "file_ids": []
    }
  ]
}

Response: {
  "id": "thread_...",
  "object": "thread",
  "created_at": 1234567890,
  "metadata": {}
}
```

### Add Message to Thread
```http
POST /assistant-communication/threads/{thread_id}/messages?assistant_id={assistant_id}
Content-Type: application/json

{
  "content": "What is FastAPI?",
  "file_ids": []
}

Response: {
  "id": "msg_...",
  "thread_id": "thread_...",
  "role": "user",
  "content": [...],
  "created_at": 1234567890
}
```

### List Thread Messages
```http
GET /assistant-communication/threads/{thread_id}/messages?assistant_id={assistant_id}

Response: [
  {
    "id": "msg_...",
    "thread_id": "thread_...",
    "role": "user",
    "content": [...],
    "created_at": 1234567890
  }
]
```

### Create Run
```http
POST /assistant-communication/threads/{thread_id}/runs
Content-Type: application/json

{
  "assistant_id": "uuid",
  "instructions": "Optional override instructions",
  "tools": []
}

Response: {
  "id": "run_...",
  "thread_id": "thread_...",
  "assistant_id": "asst_...",
  "status": "queued",
  ...
}
```

### Get Run Status
```http
GET /assistant-communication/threads/{thread_id}/runs/{run_id}?assistant_id={assistant_id}

Response: {
  "id": "run_...",
  "status": "completed",
  ...
}
```

### Submit Tool Outputs
```http
POST /assistant-communication/threads/{thread_id}/runs/{run_id}/submit?assistant_id={assistant_id}
Content-Type: application/json

{
  "tool_outputs": [
    {
      "tool_call_id": "call_...",
      "output": "Tool output"
    }
  ]
}

Response: {
  "id": "run_...",
  "status": "completed",
  ...
}
```

### Cancel Run
```http
POST /assistant-communication/threads/{thread_id}/runs/{run_id}/cancel?assistant_id={assistant_id}

Response: {
  "id": "run_...",
  "status": "cancelled",
  ...
}
```

### Get Chat Session Messages
```http
GET /assistant-communication/chat-sessions/{session_id}/messages?assistant_id={assistant_id}&limit=50&offset=0

Response: [
  {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "Hello!",
    "created_at": "2024-02-21T12:00:00Z",
    "tokens_used": 0,
    "metadata": {}
  }
]
```

### Get Messages from Multiple Sessions
```http
GET /assistant-communication/chat-sessions/messages?assistant_id={assistant_id}&limit=50&offset=0&session_ids=uuid1,uuid2

Response: [
  {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Hi! How can I help you?",
    "created_at": "2024-02-21T12:00:00Z",
    "tokens_used": 0,
    "metadata": {}
  }
]
```

### Delete Chat Session
```http
DELETE /assistant-communication/chat-sessions/{session_id}?assistant_id={assistant_id}

Response: 204 No Content
```

## Error Handling

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Invalid or missing authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error Response Format:
```json
{
  "detail": "Error message or object"
}
```

## Pagination

Endpoints that return lists support pagination using `limit` and `offset` query parameters:

- `limit`: Maximum number of items to return (default: 50, max: 100)
- `offset`: Number of items to skip (default: 0)

## Best Practices

1. Always handle error responses appropriately
2. Implement proper token management and refresh mechanisms
3. Use appropriate loading states while waiting for responses
4. Implement proper error boundaries in the UI
5. Cache responses when appropriate
6. Implement proper retry mechanisms for failed requests
7. Use proper typing for request/response data

## WebSocket Events (Coming Soon)

WebSocket support for real-time updates will be added in future versions. 