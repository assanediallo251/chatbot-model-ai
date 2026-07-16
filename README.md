# Chatbot IA ISI

MVP RAG pour l'Institut Superieur d'Informatique: upload PDF, extraction texte, embeddings, recherche semantique avec PostgreSQL + PgVector, et reponse finale via GroqCloud.

## Fonctionnalites

- API FastAPI documentee avec Swagger: `http://localhost:8000/docs`
- Upload d'un ou plusieurs PDF
- Extraction et decoupage du texte
- Embeddings locaux avec SentenceTransformers
- Stockage vectoriel PostgreSQL + PgVector
- Recherche semantique des passages pertinents
- Generation de reponse via GroqCloud
- Interface Streamlit: `http://localhost:8501`

## Prerequis

- Python 3.11+
- Docker et Docker Compose
- Une cle API GroqCloud

## Lancement avec Docker

```bash
cp .env.example .env
# renseigner GROQ_API_KEY dans .env
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`
- PostgreSQL: `localhost:5432`

## Lancement local sans Docker pour l'API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d postgres
python3 -m alembic upgrade head
python3 -m uvicorn app.main:app --reload
```

Dans un second terminal:

```bash
python3 -m streamlit run streamlit_app/main.py
```

## Endpoints principaux

- `GET /api/v1/health`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `DELETE /api/v1/documents/{document_id}`
- `POST /api/v1/chat/ask`

Exemple question:

```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est l objectif du projet ?"}'
```

## Tests et qualite

```bash
make lint
make test
```

## Notes techniques

- Le modele d'embedding par defaut est `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` avec 384 dimensions.
- Le modele Groq par defaut est `openai/gpt-oss-20b`.
- Streamlit consomme uniquement l'API FastAPI.
- Les PDF ne sont pas stockes bruts en V1; seuls les chunks, metadonnees et embeddings sont conserves.
