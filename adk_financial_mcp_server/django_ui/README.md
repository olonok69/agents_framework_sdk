# Django UI for MCP Stock Analyzer

This replaces the previous Streamlit frontend and calls the same FastAPI backend endpoints.

## Run

1. Install dependencies:

```bash
pip install -r ../requirements_adk_django.txt
```

If you use `ADK_MODEL_ID=openai/...`, ensure provider extensions are present:

```bash
pip install "google-adk[extensions]" "litellm>=1.75.5"
```

2. Start backend API (from repository root):

```bash
uvicorn stock_analyzer_bot.api:app --reload --host 0.0.0.0 --port 8000
```

3. Start Django UI:

```bash
cd django_ui
python manage.py migrate
python manage.py runserver 0.0.0.0:8501
```

4. Open:

- http://127.0.0.1:8501/
