# Chatbot IA ISI

MVP RAG pour l'Institut Superieur d'Informatique: upload PDF, extraction texte, embeddings, recherche semantique avec PostgreSQL + PgVector, et reponse finale via GroqCloud.

## Fonctionnalites

- API FastAPI documentee avec Swagger: `http://localhost:8000/docs`
- Upload d'un ou plusieurs PDF
- Extraction et decoupage du texte
- Embeddings rapides locaux par hashing, sans telechargement au premier appel
- SentenceTransformers activable en option pour une meilleure recherche semantique
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
python3 -m uvicorn app.main:app --reload --reload-dir app
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

## Performance

Le mode par defaut est optimise pour le developpement local:

```env
EMBEDDING_PROVIDER=hashing
```

Ce mode ne telecharge aucun modele HuggingFace et evite le chargement de Torch pendant une requete. L'upload PDF repond rapidement avec un statut `processing`; l'indexation continue ensuite en arriere-plan.

Pour une meilleure qualite semantique avec SentenceTransformers:

```bash
python3 -m pip install -e ".[dev,ml]"
```

Puis dans `.env`:

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_PRELOAD_ON_STARTUP=true
```

Le prechargement de modele peut aussi etre fait explicitement:

```bash
python3 -m scripts.preload_models
```

## Notes techniques

- Le provider d'embedding par defaut est `hashing` avec 384 dimensions.
- Le modele SentenceTransformers optionnel est `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Le modele Groq par defaut est `openai/gpt-oss-20b`.
- Streamlit consomme uniquement l'API FastAPI.
- Les PDF ne sont pas stockes bruts en V1; seuls les chunks, metadonnees et embeddings sont conserves.
