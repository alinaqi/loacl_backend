# LOACL Backend

Local OpenAI Assistant API Backend

## Description

LOACL Backend is a FastAPI-based service that provides a local interface to the OpenAI Assistant API with additional features and integrations.

## Features

- FastAPI-based REST API
- OpenAI Assistant API integration
- Supabase database integration
- Structured logging
- Comprehensive test suite
- API documentation (Swagger/ReDoc)

## Requirements

- Python 3.8+
- Supabase account
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Set the following environment variables in `.env`:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_api_key
```

## Development

1. Start the development server:
   ```bash
   uvicorn src.app.main:app --reload
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run linting:
   ```bash
   black .
   isort .
   pylint src tests
   ```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── src/
│   └── app/
│       ├── api/        # API endpoints
│       ├── core/       # Core functionality
│       ├── db/         # Database models and utilities
│       ├── models/     # Pydantic models
│       ├── services/   # Business logic
│       └── utils/      # Utility functions
├── tests/              # Test suite
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## License

[License Name] - See LICENSE file for details 