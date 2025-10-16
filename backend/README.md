# Practus AI Platform - Backend

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Update `.env` with your Gemini API key

3. Run the server:
```bash
python main.py
```

Server runs on http://localhost:8000

## API Endpoints

- POST /api/auth/login
- POST /api/datasource/upload
- GET /api/datasource/list
- GET /api/datasource/preview/{id}
- POST /api/ai/analyze
- GET /api/visualizations/funnel
- GET /api/insights/problems
- GET /api/devmode/recommend-model

