# 🧠 RAG Agent — Document Intelligence Chatbot

A production-ready **Retrieval-Augmented Generation (RAG)** agent built with Flask. Upload documents, ask questions, and get precise answers grounded in your content.

---

## ✨ Features

- **RAG Pipeline** — Chunks documents, retrieves relevant context via keyword search, feeds it to Claude
- **Multi-document support** — Upload multiple files per session
- **Live chat UI** — Streaming-style conversation with RAG attribution badges
- **File upload + paste** — Supports `.txt`, `.md`, `.py`, `.js`, `.html`, `.css`, `.json`, `.csv`
- **Session isolation** — Each browser session has its own document store
- **REST API** — Clean Flask endpoints for `/chat`, `/upload`, `/documents`

---

## 🚀 Local Setup

### 1. Clone / Download the project

```bash
cd rag-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here   # Mac/Linux
set GEMINI_API_KEY=sk-ant-your-key-here       # Windows CMD
```

### 5. Run the app

```bash
python app.py
```

Visit: **http://localhost:7860**

---

## 🌐 Deploy to Hugging Face Spaces

### Step 1 — Create a new Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **Create new Space**
3. Set:
   - **SDK**: `Docker`
   - **Visibility**: Public

### Step 2 — Add files

Upload these files to your Space repository:
```
app.py
requirements.txt
templates/
  index.html
```

### Step 3 — Add the Dockerfile

Create `Dockerfile` in the root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "app:app"]
```

### Step 4 — Set your secret

In your Space → **Settings** → **Repository secrets**:

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-your-key-here` |

### Step 5 — Push and deploy

```bash
git init
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git add .
git commit -m "Initial RAG Agent"
git push origin main
```

Your app will be live at:  
`https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space`

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Chat UI |
| `/chat` | POST | Send message, get AI response |
| `/upload` | POST | Upload/index a document |
| `/documents` | GET | List indexed documents |
| `/documents/clear` | DELETE | Clear all documents |
| `/chat/clear` | DELETE | Clear chat history |
| `/health` | GET | Health check |

### `/chat` example

```json
POST /chat
{ "message": "What is the main topic of my document?" }

Response:
{
  "response": "Based on your document...",
  "sources_used": 2,
  "docs_available": 3,
  "rag_active": true
}
```

---

## 🏗 Architecture

```
User Message
    │
    ▼
┌─────────────────────────────────────┐
│  Flask /chat endpoint               │
│                                     │
│  1. Retrieve session documents      │
│  2. Chunk search (keyword scoring)  │
│  3. Top-K context retrieval         │
│  4. Build RAG system prompt         │
│  5. Send to gemini     │
│  6. Return response + metadata      │
└─────────────────────────────────────┘
    │
    ▼
AI Response with source attribution
```

---

## 📁 Project Structure

```
rag-agent/
├── app.py              # Flask backend + RAG logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # For Hugging Face deployment
├── README.md           # This file
├── uploads/            # Temporary file storage
└── templates/
    └── index.html      # Chat UI (single file)
```

---

## 💡 How RAG Works Here

1. **Chunking** — Documents are split into 500-word overlapping chunks
2. **Retrieval** — For each query, chunks are scored by keyword overlap
3. **Augmentation** — Top 3 chunks per document are injected into the system prompt
4. **Generation** — Gemini answers using the retrieved context + its own knowledge
