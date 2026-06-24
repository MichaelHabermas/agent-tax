"""In-memory session state for the prototype chat loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from agent_tax.core.models import Answers, LineItems, Taxpayer, W2
from agent_tax.obs.trace import TraceLog


@dataclass
class SessionState:
    id: str
    phase: str = "awaiting_upload"
    question_count: int = 0
    w2: W2 | None = None
    answers: dict[str, object] = field(default_factory=dict)
    lines: LineItems | None = None
    taxpayer: Taxpayer | None = None
    pdf_bytes: bytes | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    trace: TraceLog = field(default_factory=TraceLog)

    def answer_model(self) -> Answers:
        return Answers(
            filing_status=str(self.answers.get("filing_status", "single")),  # type: ignore[arg-type]
            can_be_claimed_as_dependent=bool(self.answers.get("can_be_claimed_as_dependent", False)),
            other_income_acknowledged=bool(self.answers.get("other_income_acknowledged", True)),
            take_standard_deduction=bool(self.answers.get("take_standard_deduction", True)),
        )

    def summary(self) -> dict[str, object]:
        refund = self.lines.l35a_refund if self.lines else Decimal("0")
        owed = self.lines.l37_amount_owed if self.lines else Decimal("0")
        return {
            "id": self.id,
            "phase": self.phase,
            "question_count": self.question_count,
            "ready": self.pdf_bytes is not None,
            "refund": str(refund),
            "owed": str(owed),
        }


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def create(self) -> SessionState:
        session = SessionState(id=uuid4().hex)
        session.trace.add("session_created", session_id=session.id)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)


store = SessionStore()
