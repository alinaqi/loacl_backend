# Frontend API Guide

This document outlines all the available API endpoints for the LOACL frontend application.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### Register User
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

### Login
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

All subsequent requests should include the access token in the Authorization header:
```
Authorization: Bearer eyJ...
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
  "tools_enabled": ["code_interpreter"]
}

Response: {
  "id": "uuid",
  "name": "Test Assistant",
  "description": "A helpful assistant",
  ...
}
```

### Update Assistant Settings
```http
PUT /assistants/{assistant_id}
Content-Type: application/json

{
  "theme": {
    "primary_color": "#FF0000",
    "secondary_color": "#00FF00",
    "text_color": "#0000FF",
    "background_color": "#FFFFFF"
  },
  "chat_bubble_text": "Chat with me!",
  "initial_message": "Hello! How can I help you today!"
}

Response: {
  "id": "uuid",
  "theme": {...},
  ...
}
```

### Get Widget Code
```http
GET /assistants/{assistant_id}/embed

Response: {
  "code": "<script>...</script>"
}
```

### Get Widget Settings
```http
GET /assistants/{assistant_id}

Response: {
  "id": "uuid",
  "name": "Test Assistant",
  "theme": {...},
  ...
}
```

### Delete Assistant
```http
DELETE /assistants/{assistant_id}

Response: {
  "success": true
}
```

## Chat Communication

### Create Thread
```http
POST /assistant-communication/threads?assistant_id={assistant_id}
Content-Type: application/json

{
  "messages": [
    {
      "content": "Hello!",
      "file_ids": []  // Optional
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
  "file_ids": []  // Optional
}

Response: {
  "id": "msg_...",
  "thread_id": "thread_...",
  "role": "user",
  "content": [...],
  "created_at": 1234567890
}
```

### Create Run
```http
POST /assistant-communication/threads/{thread_id}/runs
Content-Type: application/json

{
  "assistant_id": "uuid",
  "instructions": "Optional override instructions",
  "tools": []  // Optional
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

### Get Thread Messages
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

### Cancel Run
```http
POST /assistant-communication/threads/{thread_id}/runs/{run_id}/cancel?assistant_id={assistant_id}

Response: {
  "id": "run_...",
  "status": "cancelled",
  ...
}
```

## Chat Sessions and Messages

### Get Session Messages
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