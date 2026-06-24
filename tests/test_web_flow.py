from pathlib import Path
import io

from fastapi.testclient import TestClient
from pypdf import PdfReader

from agent_tax.main import app


def test_upload_chat_download_trace_flow():
    client = TestClient(app)
    with Path("assets/w2_filled_sample_2025.pdf").open("rb") as file:
        upload = client.post("/upload", files={"file": ("w2.pdf", file, "application/pdf")})

    assert upload.status_code == 200
    body = upload.json()
    session_id = body["session"]["id"]
    assert body["session"]["question_count"] == 1
    assert "filing status" in body["message"]

    for answer in ["single", "no", "no", "yes"]:
        response = client.post("/chat", data={"session_id": session_id, "message": answer})
        assert response.status_code == 200

    complete = response.json()
    assert complete["session"]["phase"] == "complete"
    assert complete["session"]["question_count"] == 4
    assert complete["session"]["ready"] is True
    assert complete["session"]["refund"] == "615.00"

    download = client.get(f"/download/{session_id}")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF-")
    assert len(PdfReader(io.BytesIO(download.content)).pages) == 2

    trace = client.get(f"/trace/{session_id}").json()["trace"]
    events = [event["event"] for event in trace]
    assert "tool_call" in events
    assert "tool_result" in events


def test_other_income_guardrail_blocks_return():
    client = TestClient(app)
    with Path("assets/w2_filled_sample_2025.pdf").open("rb") as file:
        upload = client.post("/upload", files={"file": ("w2.pdf", file, "application/pdf")})

    session_id = upload.json()["session"]["id"]
    client.post("/chat", data={"session_id": session_id, "message": "single"})
    client.post("/chat", data={"session_id": session_id, "message": "no"})
    blocked = client.post("/chat", data={"session_id": session_id, "message": "yes"})

    assert blocked.status_code == 200
    assert blocked.json()["session"]["phase"] == "blocked"
    assert "should not silently prepare an incomplete return" in blocked.json()["message"]
    assert client.get(f"/download/{session_id}").status_code == 404


def test_defaults_phrase_completes_return():
    client = TestClient(app)
    with Path("assets/w2_filled_sample_2025.pdf").open("rb") as file:
        upload = client.post("/upload", files={"file": ("w2.pdf", file, "application/pdf")})

    session_id = upload.json()["session"]["id"]
    response = client.post("/chat", data={"session_id": session_id, "message": "Give me the thing."})

    assert response.status_code == 200
    assert response.json()["session"]["phase"] == "complete"
    assert response.json()["session"]["ready"] is True
    assert response.json()["session"]["refund"] == "615.00"
    assert client.get(f"/download/{session_id}").status_code == 200
