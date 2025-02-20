# LOACL API Endpoints Documentation

## Base URL
```
/api/v1
```

## Authentication Endpoints

### Assistant Authentication
```http
POST /auth/initialize
```
Initialize an assistant session with OpenAI Assistant ID and API key
- Request Body:
  ```json
  {
    "assistant_id": "string",
    "api_key": "string",
    "configuration": {
      "temperature": float,
      "custom_instructions": "string",
      "tools_enabled": ["string"]
    }
  }
  ```

### User Authentication (Optional)
```http
POST /auth/token
```
Get authentication token for persistent user sessions (optional)
- Request Body:
  ```json
  {
    "client_id": "string",
    "client_secret": "string"
  }
  ```

### Guest Session
```http
POST /auth/guest
```
Create a temporary guest session
- Request Body:
  ```json
  {
    "fingerprint": "string",  // Optional browser fingerprint
    "metadata": {}  // Optional metadata about the session
  }
  ```
- Response:
  ```json
  {
    "session_id": "string",
    "expires_at": "timestamp",
    "temporary_token": "string"
  }
  ```

## Conversation Management

### Thread Management
```http
POST /threads
```
Create a new conversation thread
- Request Body:
  ```json
  {
    "session_type": "guest|authenticated",  // Specify if guest or authenticated session
    "session_id": "string",  // Required for guest sessions
    "metadata": {}  // Optional metadata
  }
  ```
- Response: Thread ID and initial state

```http
GET /threads/{thread_id}
```
Get thread details and history
- Query Parameters:
  - session_id: string (required for guest sessions)

```http
DELETE /threads/{thread_id}
```
Delete a conversation thread
- Query Parameters:
  - session_id: string (required for guest sessions)

### Message Management
```http
POST /threads/{thread_id}/messages
```
Send a message in a thread
- Request Body:
  ```json
  {
    "content": "string",
    "files": ["file_ids"],
    "metadata": {},
    "session_id": "string"  // Required for guest sessions
  }
  ```

```http
GET /threads/{thread_id}/messages
```
Get messages in a thread
- Query Parameters:
  - limit: int
  - before: timestamp
  - after: timestamp
  - session_id: string (required for guest sessions)

### Guest Session Management
```http
GET /guest/sessions/{session_id}/threads
```
Get all threads associated with a guest session

```http
DELETE /guest/sessions/{session_id}
```
Delete a guest session and all associated data

### Session Conversion
```http
POST /auth/convert-session
```
Convert a guest session to an authenticated session
- Request Body:
  ```json
  {
    "session_id": "string",
    "user_credentials": {
      "client_id": "string",
      "client_secret": "string"
    }
  }
  ```

## Session Security and Limitations

### Guest Sessions
- Temporary sessions expire after 24 hours of inactivity
- Limited to 10 active threads per session
- Basic rate limiting applied
- File upload size restrictions
- No access to advanced features (webhooks, custom configurations)

### Authenticated Sessions
- Persistent sessions with no expiration
- Higher rate limits
- Larger file upload allowances
- Access to all features
- Custom configurations and preferences

## File Management

### File Operations
```http
POST /files
```
Upload a file
- Multipart form data

```http
GET /files/{file_id}
```
Get file metadata

```http
GET /files/{file_id}/content
```
Download file content

```http
DELETE /files/{file_id}
```
Delete a file

## Assistant Management

### Configuration
```http
GET /assistant/configuration
```
Get current assistant configuration

```http
PATCH /assistant/configuration
```
Update assistant configuration
- Request Body:
  ```json
  {
    "temperature": float,
    "custom_instructions": "string",
    "tools_enabled": ["string"]
  }
  ```

### Guided Questions
```http
GET /assistant/guided-questions
```
Get initial guided questions

```http
POST /threads/{thread_id}/suggest
```
Get follow-up suggestions based on conversation
- Response:
  ```json
  {
    "suggestions": ["string"]
  }
  ```

## Voice Integration

### Speech Processing
```http
POST /speech/text
```
Convert speech to text
- Request: Audio file
- Response: Transcribed text

```http
POST /speech/audio
```
Convert text to speech
- Request Body:
  ```json
  {
    "text": "string",
    "voice_id": "string"
  }
  ```
- Response: Audio file

## Analytics & Monitoring

### Usage Statistics
```http
GET /analytics/usage
```
Get usage statistics
- Query Parameters:
  - start_date: date
  - end_date: date
  - metrics: ["string"]

### Health Check
```http
GET /health
```
Get service health status

```http
GET /health/detailed
```
Get detailed service health metrics

## User Preferences

### Preferences Management
```http
GET /preferences
```
Get user preferences

```http
PATCH /preferences
```
Update user preferences
- Request Body:
  ```json
  {
    "language": "string",
    "theme": "string",
    "notifications_enabled": boolean,
    "custom_settings": {}
  }
  ```

## Webhook Management

### Webhook Configuration
```http
POST /webhooks
```
Register a new webhook
- Request Body:
  ```json
  {
    "url": "string",
    "events": ["string"],
    "secret": "string"
  }
  ```

```http
GET /webhooks
```
List registered webhooks

```http
DELETE /webhooks/{webhook_id}
```
Delete a webhook

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {},
  "metadata": {
    "timestamp": "string",
    "request_id": "string"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  },
  "metadata": {
    "timestamp": "string",
    "request_id": "string"
  }
}
```

## Rate Limiting
- All endpoints are rate-limited
- Rate limit headers included in responses:
  - X-RateLimit-Limit
  - X-RateLimit-Remaining
  - X-RateLimit-Reset

## Authentication
- Endpoints support both Bearer token and session-based authentication
- Format for authenticated users: `Authorization: Bearer <token>`
- Format for guest sessions: `X-Session-ID: <session_id>`
- All endpoints except `/auth/*`, `/health`, and guest session creation require either a valid Bearer token or session ID

## Versioning
- API version included in URL path
- Current version: v1
- Version header also supported: `Accept: application/vnd.loacl.v1+json` 