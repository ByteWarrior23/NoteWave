import json
import os
import shutil
import threading
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

from rag import (
    analyze_full_document,
    chat_with_context,
    delete_document_data,
    generate_debate,
    generate_flashcards,
    generate_podcast_script,
    generate_quiz,
    generate_vault_audit,
    get_configured_keys_count,
    get_provider_info,
    process_pdf,
    query_documents,
    stream_chat_answer,
    validate_api_key,
)
from key_pool import KEY_POOL, is_rate_limit_error
from tts import audio_to_base64, synthesize_line

DEFAULT_API_KEY = os.getenv("GOOGLE_API_KEY", "")

app = FastAPI(title="NoteWave + AI Knowledge Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def resolve_api_key(api_key: Optional[str]) -> str:
    key = (api_key or "").strip()
    if key:
        return key
    if KEY_POOL.has_keys():
        return KEY_POOL.next_key()
    if DEFAULT_API_KEY:
        return DEFAULT_API_KEY
    raise HTTPException(status_code=401, detail="Missing API Key. Please provide your Google Gemini API key.")


def handle_api_error(e: Exception):
    if is_rate_limit_error(e):
        raise HTTPException(
            status_code=429,
            detail="API quota exceeded. Wait a moment or add more Gemini keys in Settings.",
        )
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "NoteWave Knowledge Hub",
        "keys_configured": get_configured_keys_count(),
        "provider": get_provider_info(),
    }


# --- REQUEST MODELS ---
class KeyValidationRequest(BaseModel):
    api_key: str


class SearchQuery(BaseModel):
    query: str
    api_key: Optional[str] = None
    filename: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    api_key: Optional[str] = None
    fileId: Optional[str] = None
    filename: Optional[str] = None


class StudioRequest(BaseModel):
    fileId: Optional[str] = None
    filename: Optional[str] = None
    api_key: Optional[str] = None
    count: Optional[int] = 5


class TTSRequest(BaseModel):
    text: str
    speaker: str = "Host"
    api_key: Optional[str] = None


# --- KEY VALIDATION ---
@app.post("/validate-key")
@app.post("/api/validate-key")
def validate_key_endpoint(request: KeyValidationRequest):
    result = validate_api_key(request.api_key)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid API Key."))
    return {"status": "Connected", "model": result.get("model")}


# --- UPLOAD & INGEST (lazy: only embed, no studio generation) ---
@app.post("/upload")
@app.post("/api/upload")
@app.post("/api/ingest")
async def upload_document(
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    resolved_key = resolve_api_key(api_key)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        num_chunks = process_pdf(file_path, resolved_key)

        return {
            "success": True,
            "filename": file.filename,
            "name": file.filename,
            "status": "Indexed",
            "chunks": num_chunks,
            "message": "Document indexed. Open studios to generate content on demand.",
        }

    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        handle_api_error(e)


# --- DOCUMENTS MANAGEMENT ---
@app.get("/documents")
@app.get("/api/documents")
def list_documents():
    docs = []
    if os.path.exists(UPLOAD_FOLDER):
        for f in os.listdir(UPLOAD_FOLDER):
            if f.lower().endswith(".pdf"):
                fp = os.path.join(UPLOAD_FOLDER, f)
                stat = os.stat(fp)
                docs.append({
                    "id": int(stat.st_mtime * 1000),
                    "name": f,
                    "filename": f,
                    "size": stat.st_size,
                    "date": "Uploaded",
                    "mastery": 85,
                })
    return {"documents": docs}


@app.delete("/documents/{filename}")
@app.delete("/api/documents/{filename}")
@app.post("/api/delete")
def delete_document_endpoint(
    filename: Optional[str] = None,
    request: Optional[StudioRequest] = None,
    api_key: Optional[str] = None,
):
    target = filename
    if not target and request:
        target = request.fileId or request.filename
    if not target:
        raise HTTPException(status_code=400, detail="Filename required.")

    resolved_key = None
    try:
        resolved_key = resolve_api_key(api_key or (request.api_key if request else None))
    except HTTPException:
        pass

    delete_document_data(target, api_key=resolved_key)
    return {"success": True, "deleted": target}


# --- SEARCH & CHAT ---
@app.post("/search")
@app.post("/api/search")
def search_knowledge_base(request: SearchQuery):
    resolved_key = resolve_api_key(request.api_key)
    try:
        answer = query_documents(request.query, resolved_key, filename=request.filename)
        return {"results": [answer]}
    except Exception as e:
        handle_api_error(e)


@app.post("/chat")
@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename
    try:
        job = start_chat_job(request.messages, resolved_key, target_file)
        return {"job_id": job["id"], "status": "queued", "message": "queued"}
    except Exception as e:
        handle_api_error(e)


# --- CHAT JOB QUEUE (polling-based progress) ---
_chat_jobs: Dict[str, Dict[str, Any]] = {}
_chat_jobs_lock = threading.Lock()


def start_chat_job(messages: List[Dict[str, str]], resolved_key: str, target_file: Optional[str]):
    job_id = uuid.uuid4().hex
    job = {"id": job_id, "status": "queued", "message": "queued", "reply": None}
    with _chat_jobs_lock:
        _chat_jobs[job_id] = job

    def _worker():
        def _set_status(message: str):
            with _chat_jobs_lock:
                if job_id in _chat_jobs:
                    _chat_jobs[job_id]["status"] = message
                    _chat_jobs[job_id]["message"] = message

        try:
            _set_status("Searching your knowledge base...")
            reply = chat_with_context(messages, resolved_key, filename=target_file, status_cb=_set_status)
            with _chat_jobs_lock:
                job["status"] = "done"
                job["message"] = "done"
                job["reply"] = reply
        except Exception as e:
            detail = str(e)
            if is_rate_limit_error(e):
                detail = "API quota exceeded. Wait a moment or add more Gemini keys in Settings."
            with _chat_jobs_lock:
                job["status"] = "error"
                job["message"] = detail
                job["reply"] = None

    threading.Thread(target=_worker, daemon=True).start()
    return job


@app.get("/chat/status/{job_id}")
@app.get("/api/chat/status/{job_id}")
def chat_status_endpoint(job_id: str):
    with _chat_jobs_lock:
        job = _chat_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Chat job not found or expired.")
    if job["status"] == "done":
        return {"status": "done", "role": "assistant", "content": job["reply"], "text": job["reply"]}
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job["message"])
    return {"status": "working", "message": job["message"]}


@app.post("/chat/stream")
@app.post("/api/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename

    def _events():
        try:
            for evt in stream_chat_answer(request.messages, resolved_key, filename=target_file):
                if "status" in evt:
                    yield f"event: status\ndata: {json.dumps({'type': 'status', 'message': evt['status']})}\n\n"
                elif "token" in evt:
                    yield f"data: {json.dumps({'type': 'token', 'text': evt['token']})}\n\n"
                elif "error" in evt:
                    yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': evt['error']})}\n\n"
                    return
                elif "done" in evt:
                    yield f"event: done\ndata: {json.dumps({'type': 'done'})}\n\n"
                    return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(_events(), media_type="text/event-stream")


# --- TTS (ElevenLabs) ---
@app.post("/tts")
@app.post("/api/tts")
async def tts_endpoint(request: TTSRequest):
    try:
        audio = await synthesize_line(request.text, request.speaker)
        if audio:
            return {"audio": audio_to_base64(audio), "format": "audio/mpeg"}
        raise HTTPException(status_code=503, detail="TTS unavailable. Using browser speech fallback.")
    except HTTPException:
        raise
    except Exception as e:
        handle_api_error(e)


# --- STUDIOS ---
@app.post("/podcast")
@app.post("/api/podcast")
def podcast_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        script = generate_podcast_script(target_file, resolved_key)
        return {"script": script}
    except Exception as e:
        handle_api_error(e)


@app.post("/debate")
@app.post("/api/debate")
def debate_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        transcript = generate_debate(target_file, resolved_key)
        return {"transcript": transcript}
    except Exception as e:
        handle_api_error(e)


@app.post("/vault")
@app.post("/api/vault")
@app.post("/api/vault/audit")
def vault_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        audit = generate_vault_audit(target_file, resolved_key)
        return audit
    except Exception as e:
        handle_api_error(e)


@app.post("/quiz")
@app.post("/api/quiz")
def quiz_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        questions = generate_quiz(target_file, resolved_key, count=request.count or 5)
        return {"questions": questions}
    except Exception as e:
        handle_api_error(e)


@app.post("/flashcards")
@app.post("/api/flashcards")
def flashcards_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        cards = generate_flashcards(target_file, resolved_key)
        return {"flashcards": cards}
    except Exception as e:
        handle_api_error(e)


@app.post("/graph")
@app.post("/api/graph_removed")
@app.post("/api/graph_removed/extract")
def graph_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        return graph_data
    except Exception as e:
        handle_api_error(e)


@app.post("/summary")
@app.post("/api/summary")
def summary_endpoint(request: StudioRequest):
    resolved_key = resolve_api_key(request.api_key)
    target_file = request.fileId or request.filename or ""
    try:
        analysis = analyze_full_document(target_file, resolved_key)
        return {"summary": analysis.get("summary", "")}
    except Exception as e:
        handle_api_error(e)
