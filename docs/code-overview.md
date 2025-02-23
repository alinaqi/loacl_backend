# LOACL Backend Code Overview

## Project Overview

LOACL (Lightweight OpenAI Assistants ChatBot Library) is a backend service that enables easy integration of OpenAI's Assistants API into any application. It provides:

- User authentication and management
- API key management for client applications
- OpenAI Assistant management and configuration
- Real-time chat functionality with streaming responses
- Embedding capabilities for web applications

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: Backend-as-a-Service for database and authentication
- **OpenAI API**: For AI assistant functionality
- **Python 3.12+**: Latest Python version for better performance and features

## Core Development Rules

### 1. Database Access

- Use Supabase directly; NO SQLAlchemy or other ORMs
- All database operations should use the Supabase client
- Always use RLS (Row Level Security) policies for data access
- Example:
  ```python
  # ✅ Correct way
  supabase = get_supabase_client()
  result = supabase.table("table_name").select("*").execute()

  # ❌ Wrong way - Don't use SQLAlchemy
  db.query(Model).all()
  ```

### 2. Authentication & Authorization

- Use Supabase Auth for user management
- JWT tokens for API authentication
- API keys for client application authentication
- Always validate user permissions through RLS policies

### 3. Code Structure

```
src/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/    # API route handlers
│   │       └── api.py       # Main router
│   ├── core/               # Core configurations
│   ├── schemas/           # Pydantic models
│   └── services/         # Business logic
├── tests/               # Test files
└── docs/              # Documentation
```

### 4. API Endpoint Rules

- Use async/await for all endpoint handlers
- Implement proper error handling
- Use Pydantic models for request/response validation
- Example:
  ```python
  @router.post("", response_model=ResponseModel)
  async def create_resource(
      data: RequestModel,
      current_user: User = Depends(deps.get_current_user),
  ) -> ResponseModel:
      try:
          result = supabase.table("table").insert(data.model_dump()).execute()
          return ResponseModel(**result.data[0])
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
  ```

### 5. Schema Design

- Keep schemas minimal - only include necessary fields
- Use UUID for primary keys
- Always include created_at timestamps
- Add is_active boolean for soft deletes
- Example:
  ```sql
  create table if not exists table_name (
      id uuid default gen_random_uuid() primary key,
      user_id uuid not null,
      name text not null,
      created_at timestamp with time zone default now(),
      is_active boolean default true
  );
  ```

### 6. Security Rules

- Never expose sensitive data in responses
- Always use RLS policies for table access
- Hash/encrypt sensitive information
- Use API keys for external access
- Example RLS policy:
  ```sql
  create policy "Users can only access their own data"
  on table_name
  for all
  using (auth.uid()::uuid = user_id);
  ```

### 7. Testing

- Write tests for all endpoints
- Use separate test database
- Test both success and failure cases
- Always use test user name as ashaheen+test+<id>@workhub.ai
- Example test structure:
  ```python
  class TestFlow:
      def setup(self):
          # Setup test data
          
      def test_success_case(self):
          # Test successful operation
          
      def test_failure_case(self):
          # Test error handling
  ```

### 8. Error Handling

- Use proper HTTP status codes
- Return descriptive error messages
- Log errors appropriately
- Example:
  ```python
  if not result.data:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Resource not found"
      )
  ```

### 9. Documentation

- Add docstrings to all functions and classes
- Keep README up to date
- Document all environment variables
- Example docstring:
  ```python
  """Function description.

  Args:
      param1: Description of first parameter
      param2: Description of second parameter

  Returns:
      Description of return value

  Raises:
      HTTPException: Description of when this error is raised
  """
  ```

### 10. Environment Configuration

- Use .env files for configuration
- Never commit sensitive values
- Document all required environment variables
- Example:
  ```env
  SUPABASE_URL=your_supabase_url
  SUPABASE_KEY=your_supabase_key
  OPENAI_API_KEY=your_openai_key
  ```

## Best Practices

1. Keep code simple and minimal
2. Don't repeat yourself (DRY)
3. Use type hints everywhere
4. Follow PEP 8 style guide
5. Write self-documenting code
6. Use meaningful variable names
7. Keep functions small and focused
8. Handle errors gracefully
9. Write tests for new features
10. Document significant changes

## Commit Guidelines

- Use descriptive commit messages
- Follow conventional commits format
- Always skip pre-commit checks using `--no-verify` flag to avoid unnecessary formatting issues
- Example commit commands:
  ```bash
  # ✅ Correct way - Skip pre-commit checks
  git add .
  git commit --no-verify -m "feat: Add API key management"
  
  # ❌ Wrong way - Don't use regular commit
  git commit -m "feat: Add API key management"
  ```
- Example commit message formats:
  ```
  feat: Add API key management
  fix: Resolve streaming response issue
  docs: Update API documentation
  ``` 