# ✈️ SkyBot — RAG AI Assistant

**SkyBot** is a chatbot built using the **Retrieval-Augmented Generation (RAG)** approach.  
It allows users to upload their own documents (TXT or PDF) and ask natural language questions based strictly on their content.

It combines:
- **FastAPI** for the backend and REST API
- **LangChain** + **FAISS** for local vector-based retrieval
- **Sentence Transformers** (`all-MiniLM-L6-v2`) for embeddings
- **Groq API** (LLaMA 3.x 70B models) for answer generation

---

## 🚀 Features

| Feature | Description |
|------|------------|
| 📄 Document upload | Upload `.txt` or `.pdf` files via the web interface |
| 🔍 Semantic search | Local FAISS vector store (fast, offline retrieval) |
| 💬 RAG-based chat | Answers generated *only* from uploaded document content |
| 🕓 Conversation history | Context from the last interactions is sent to the LLM |
| 💾 Index persistence | Optional saving of the FAISS index to disk |
| 🌐 Web interface | Responsive UI with async chat bubbles and drag & drop |
| 🔌 REST API | `/ask`, `/upload`, `/status`, `/clear-history` + Swagger UI |

---

## 🛠️ Tech Stack

```
Python 3.11+
FastAPI + Uvicorn
LangChain (community)
FAISS (CPU)
Sentence Transformers (all-MiniLM-L6-v2)
Groq API (LLaMA models)
Jinja2 (HTML templates)
Ruff (linting & formatting)
Pytest (testing)
```

---

## ⚡ Local Installation & Run

### 1. Prerequisites
- Python 3.11+
- A free Groq API key: https://console.groq.com

### 2. Clone & setup

```bash
git clone https://github.com/YOUR_USERNAME/skybot.git
cd skybot

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
# Open .env and set your GROQ_API_KEY
```

### 4. Run the development server

```bash
make dev
# or directly:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

---

## 🏗️ Build & Deployment

### Production server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

> ⚠️ **Multi-workers note**  
The chatbot uses an in-memory vector store per process.  
For multi-worker deployments, the vector store should be externalized (Redis, Qdrant, etc.).

---

### Docker (example)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t skybot .
docker run -p 8000:8000 --env-file .env skybot
```

---

## 🌍 Environment Variables

| Variable | Required | Description |
|--------|----------|------------|
| `GROQ_API_KEY` | ✅ | Groq API key |
| `GROQ_MODEL` | No | LLM model (default: `llama-3.3-70b-versatile`) |
| `GROQ_TEMPERATURE` | No | Generation temperature (default: `0.3`) |
| `GROQ_MAX_TOKENS` | No | Max tokens per answer (default: `1500`) |
| `FAISS_INDEX_DIR` | No | FAISS index directory (default: `faiss_index`) |
| `CHUNK_SIZE` | No | Document chunk size (default: `1000`) |
| `RAG_TOP_K` | No | Top-K retrieved chunks (default: `4`) |

---

## 📁 Project Structure

```
skybot/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── services/
│   │   ├── chatbot.py
│   │   └── ingest.py
│   └── main.py
│
├── data/
│   └── documents/
│
├── static/
│   └── styles.css
│
├── templates/
│   └── index.html
│
├── tests/
│   └── test_routes.py
│
├── scripts/
│   └── ingest.py
│
├── .env.example
├── .gitignore
├── Makefile
├── requirements.txt
├── requirements-dev.txt
└── ruff.toml
```

---

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
make test
```

---

## 🔌 API Reference

### `GET /`
Main HTML page

### `POST /ask`
Ask a question to the chatbot.

**Example**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Accept: application/json" \
  -F "question=What aircraft types are used?"
```

---

### `POST /upload`
Upload a document and rebuild the index.

---

### `GET /status`
Health check endpoint.

---

### `POST /clear-history`
Reset conversation history.

---

### Swagger UI
http://localhost:8000/docs

---

## 📄 License
MIT License

---

## 👩‍💻 Author

**Wiam Rabie**  
AI & Data Engineering Student  
