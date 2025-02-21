# LOACL - Local OpenAI Assistant Chat Library

LOACL is a FastAPI-based backend service that provides a wrapper around OpenAI's Assistants API, enabling local management of chat widgets and conversations.

## Features

- User registration and authentication
- Chat widget creation and management
- Integration with OpenAI Assistants API
- Conversation history tracking
- Real-time chat capabilities

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (for production)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/loacl.git
cd loacl
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```
Then edit `.env` with your configuration.

### Running the Application

For development:
```bash
uvicorn src.app.main:app --reload
```

For production:
```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest
```

## API Documentation

Once the application is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
src/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   └── settings.py
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
└── main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 