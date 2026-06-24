"""FastAPI app for the Agentic Tax-Filing Assistant."""
from __future__ import annotations

import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from agent_tax.agent.loop import handle_user_message, start_after_upload
from agent_tax.web.session import store

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

APP_TITLE = "Agentic Tax-Filing Assistant"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-5.5")
TRACE_ENABLED = os.getenv("TRACE_ENABLED", "true").lower() == "true"

app = FastAPI(title=APP_TITLE)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "model": LLM_MODEL,
            "api_key_configured": bool(os.getenv("OPENROUTER_API_KEY")),
            "trace_enabled": TRACE_ENABLED,
        }
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.post("/session")
def create_session() -> JSONResponse:
    session = store.create()
    return JSONResponse(session.summary())


@app.post("/upload")
async def upload_w2(file: UploadFile = File(...), session_id: str | None = Form(default=None)) -> JSONResponse:
    session = store.get(session_id) if session_id else store.create()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if file.content_type not in {None, "application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a PDF W-2.")
    try:
        message = start_after_upload(session, await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({"session": session.summary(), "message": message})


@app.post("/chat")
def chat(session_id: str = Form(...), message: str = Form(...)) -> JSONResponse:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        reply = handle_user_message(session, message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse({"session": session.summary(), "message": reply})


@app.get("/download/{session_id}")
def download(session_id: str) -> Response:
    session = store.get(session_id)
    if not session or not session.pdf_bytes:
        raise HTTPException(status_code=404, detail="Completed return not found")
    return Response(
        content=session.pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="completed-2025-form-1040.pdf"'},
    )


@app.get("/trace/{session_id}")
def trace(session_id: str) -> JSONResponse:
    session = store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse({"session": session.summary(), "trace": session.trace.as_list()})


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agentic Tax-Filing Assistant</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
    body { margin: 0; background: #f7f7f4; color: #1f2933; }
    main { max-width: 980px; margin: 0 auto; padding: 24px; display: grid; gap: 16px; grid-template-columns: minmax(0, 1.4fr) minmax(280px, .8fr); }
    h1 { margin: 0 0 4px; font-size: 24px; }
    p { margin: 0; }
    .top { grid-column: 1 / -1; display: flex; justify-content: space-between; gap: 16px; align-items: end; }
    .muted { color: #65717f; font-size: 14px; }
    .panel { background: #fff; border: 1px solid #ddd8cd; border-radius: 8px; padding: 16px; }
    .chat { min-height: 420px; display: flex; flex-direction: column; gap: 10px; }
    .messages { flex: 1; overflow: auto; display: flex; flex-direction: column; gap: 10px; padding-bottom: 8px; }
    .msg { max-width: 82%; padding: 10px 12px; border-radius: 8px; line-height: 1.35; }
    .assistant { background: #edf4ed; align-self: flex-start; }
    .user { background: #223047; color: white; align-self: flex-end; }
    form { display: flex; gap: 8px; flex-wrap: wrap; }
    input[type="text"] { flex: 1; min-width: 180px; padding: 10px; border: 1px solid #c9c3b8; border-radius: 6px; font: inherit; }
    input[type="file"] { max-width: 100%; }
    button, .download { border: 0; border-radius: 6px; background: #1f6f4a; color: white; padding: 10px 12px; font: inherit; cursor: pointer; text-decoration: none; display: inline-block; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .download { background: #223047; }
    pre { white-space: pre-wrap; word-break: break-word; font-size: 12px; max-height: 520px; overflow: auto; margin: 0; }
    @media (max-width: 760px) { main { grid-template-columns: 1fr; padding: 16px; } .top { display: block; } }
  </style>
</head>
<body>
<main>
  <section class="top">
    <div>
      <h1>Agentic Tax-Filing Assistant</h1>
      <p class="muted">Upload a W-2 PDF, answer four questions, download a completed 2025 Form 1040. Not tax advice.</p>
    </div>
    <a id="download" class="download" style="display:none">Download 1040</a>
  </section>

  <section class="panel chat">
    <form id="uploadForm">
      <input id="w2" type="file" accept="application/pdf" required />
      <button>Upload W-2</button>
    </form>
    <div id="messages" class="messages"></div>
    <form id="chatForm">
      <input id="message" type="text" placeholder="Type your answer..." autocomplete="off" disabled />
      <button id="send" disabled>Send</button>
    </form>
  </section>

  <aside class="panel">
    <p><strong>Observation trace</strong></p>
    <p class="muted" style="margin: 4px 0 12px;">Tool calls, guardrails, state transitions.</p>
    <pre id="trace">No session yet.</pre>
  </aside>
</main>

<script>
let sessionId = null;
const messages = document.getElementById("messages");
const trace = document.getElementById("trace");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send");
const download = document.getElementById("download");

function add(role, content) {
  const node = document.createElement("div");
  node.className = "msg " + role;
  node.textContent = content;
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
}

async function refreshTrace() {
  if (!sessionId) return;
  const res = await fetch(`/trace/${sessionId}`);
  const data = await res.json();
  trace.textContent = JSON.stringify(data.trace, null, 2);
  if (data.session.ready) {
    download.href = `/download/${sessionId}`;
    download.style.display = "inline-block";
    messageInput.disabled = true;
    sendButton.disabled = true;
  }
}

document.getElementById("uploadForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData();
  form.append("file", document.getElementById("w2").files[0]);
  if (sessionId) form.append("session_id", sessionId);
  const res = await fetch("/upload", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok) { add("assistant", data.detail || "Upload failed."); return; }
  sessionId = data.session.id;
  add("assistant", data.message);
  messageInput.disabled = false;
  sendButton.disabled = false;
  await refreshTrace();
});

document.getElementById("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text || !sessionId) return;
  add("user", text);
  messageInput.value = "";
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("message", text);
  const res = await fetch("/chat", { method: "POST", body: form });
  const data = await res.json();
  add("assistant", data.message || data.detail || "Something went wrong.");
  await refreshTrace();
});
</script>
</body>
</html>"""
