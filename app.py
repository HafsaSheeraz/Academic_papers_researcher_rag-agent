import os
import uuid
import time
from dotenv import load_dotenv
from pathlib import Path
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS

# New Gemini SDK imports
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rag-agent-secret-key-2026")
CORS(app)

# --- Initialize Gemini Client ---
# It will look for GEMINI_API_KEY in your .env or system environment
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=3) # Auto-retry on 503 errors
    )
)
# In-memory document store (per session)
document_store = {}
chat_histories = {}

ALLOWED_EXTENSIONS = {"txt", "md", "py", "js", "html", "css", "json", "csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks

def simple_search(query, chunks, top_k=3):
    query_words = set(query.lower().split())
    scored = []
    for i, chunk in enumerate(chunks):
        chunk_words = set(chunk.lower().split())
        score = len(query_words & chunk_words) / max(len(query_words), 1)
        scored.append((score, i, chunk))
    scored.sort(reverse=True)
    return [chunk for _, _, chunk in scored[:top_k]]

def get_session_id():
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_document():
    session_id = get_session_id()
    content = None
    doc_name = None

    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "" or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file"}), 400
        doc_name = file.filename
        content = file.read().decode("utf-8", errors="ignore")
    elif "text" in request.form:
        content = request.form["text"]
        doc_name = request.form.get("name", f"doc_{int(time.time())}.txt")

    if not content:
        return jsonify({"error": "No content"}), 400

    chunks = chunk_text(content)
    if session_id not in document_store:
        document_store[session_id] = []
    
    document_store[session_id].append({
        "name": doc_name,
        "chunks": chunks,
        "total_chunks": len(chunks)
    })
    return jsonify({"success": True, "message": f"Indexed {doc_name}"})
@app.route("/chat", methods=["POST"])
def chat():
    session_id = get_session_id()
    data = request.get_json()
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if session_id not in chat_histories:
        chat_histories[session_id] = []

    # RAG Retrieval Logic (Remains the same)
    context_parts = []
    docs = document_store.get(session_id, [])
    for doc in docs:
        relevant = simple_search(user_message, doc["chunks"], top_k=3)
        if relevant:
            context_parts.append(f"SOURCE: {doc['name']}\n" + "\n".join(relevant))

    if context_parts:
        context_text = "\n\n".join(context_parts)
        system_prompt = f"Use this context: {context_text}. Be concise and cite sources."
    else:
        system_prompt = "No documents found. Answer from general knowledge."

    # --- 2. Correctly Format History for the SDK ---
    # We map 'assistant' to 'model' for Gemini compatibility
    history_for_gemini = []
    for m in chat_histories[session_id][-10:]:
        history_for_gemini.append(
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part.from_text(text=m["content"])]
            )
        )

    # --- 3. Optimized Model Fallback ---
    # gemini-3.1-flash-lite is the new 2026 speed king
    # models_to_try = ["gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview"]
    models_to_try = ["gemini-3-flash-preview", "gemini-3.1-flash-lite-preview"]
    last_error = ""

    for model_name in models_to_try:
        try:
            # We use the 'chat' interface to maintain memory
            chat_session = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7
                ),
                history=history_for_gemini # <--- This gives the AI memory!
            )
            
            response = chat_session.send_message(user_message)
            assistant_message = response.text
            
            # Save to local history
            chat_histories[session_id].append({"role": "user", "content": user_message})
            chat_histories[session_id].append({"role": "assistant", "content": assistant_message})

            return jsonify({
                "response": assistant_message,
                "model_used": model_name,
                "rag_active": len(context_parts) > 0
            })

        except Exception as e:
            last_error = str(e)
            if "503" in last_error or "UNAVAILABLE" in last_error:
                continue 
            return jsonify({"error": f"AI Error: {last_error}"}), 500

    return jsonify({"error": "All models busy", "details": last_error}), 503

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "gemini-3-flash-preview"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)# import os
