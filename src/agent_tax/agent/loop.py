"""Stateful chat loop for the tax assistant."""
from __future__ import annotations

from agent_tax.agent.guardrails import (
    SCOPE_REFUSAL,
    enforce_question_budget,
    is_yes,
    parse_filing_status,
    validate_w2,
)
from agent_tax.agent.tools import compute_1040_tool, extract_w2_tool, fill_1040_pdf_tool
from agent_tax.core.models import Taxpayer
from agent_tax.web.session import SessionState


QUESTION_BY_PHASE = {
    "filing_status": (
        "I read the W-2. What filing status should I use: single, married filing jointly, "
        "married filing separately, head of household, or qualifying surviving spouse?"
    ),
    "dependent": "Can someone else claim this taxpayer as a dependent for 2025?",
    "other_income": "Besides this one W-2, did the taxpayer have any other income in 2025?",
    "standard_deduction": "Last check: should I use the standard deduction for this simple return?",
}


def _ask(session: SessionState, phase: str) -> str:
    enforce_question_budget(session.question_count)
    session.phase = phase
    session.question_count += 1
    message = QUESTION_BY_PHASE[phase]
    session.messages.append({"role": "assistant", "content": message})
    session.trace.add("question_asked", phase=phase, question_count=session.question_count, message=message)
    return message


def start_after_upload(session: SessionState, file_bytes: bytes) -> str:
    session.trace.add("tool_call", tool="extract_w2", args={"bytes": len(file_bytes)})
    w2 = extract_w2_tool(file_bytes)
    issues = validate_w2(w2)
    if issues:
        session.trace.add("guardrail_block", issues=issues)
        raise ValueError("I could read the W-2, but it failed validation: " + "; ".join(issues))

    session.w2 = w2
    session.messages.append({"role": "assistant", "content": "Got the W-2. I’ll keep this to four quick questions."})
    session.trace.add(
        "tool_result",
        tool="extract_w2",
        employee=f"{w2.employee_first_name} {w2.employee_last_name}".strip(),
        wages=str(w2.box1_wages),
        withholding=str(w2.box2_fed_withholding),
    )
    return _ask(session, "filing_status")


def handle_user_message(session: SessionState, message: str) -> str:
    session.messages.append({"role": "user", "content": message})
    session.trace.add("user_message", phase=session.phase, message=message)

    if session.phase == "awaiting_upload":
        return "Please upload the W-2 PDF first. Then I’ll ask the few questions I need."

    if session.phase == "filing_status":
        status = parse_filing_status(message)
        if not status:
            return "Use one of: single, married filing jointly, married filing separately, head of household, or qualifying surviving spouse."
        session.answers["filing_status"] = status
        session.trace.add("answer_recorded", field="filing_status", value=status)
        return _ask(session, "dependent")

    if session.phase == "dependent":
        session.answers["can_be_claimed_as_dependent"] = is_yes(message)
        session.trace.add("answer_recorded", field="can_be_claimed_as_dependent", value=session.answers["can_be_claimed_as_dependent"])
        return _ask(session, "other_income")

    if session.phase == "other_income":
        if is_yes(message):
            session.phase = "blocked"
            session.trace.add("guardrail_block", reason="other_income")
            reply = SCOPE_REFUSAL + " Because you said there is other income, I should not silently prepare an incomplete return."
            session.messages.append({"role": "assistant", "content": reply})
            return reply
        session.answers["other_income_acknowledged"] = True
        session.trace.add("answer_recorded", field="other_income_acknowledged", value=True)
        return _ask(session, "standard_deduction")

    if session.phase == "standard_deduction":
        if not is_yes(message):
            session.phase = "blocked"
            session.trace.add("guardrail_block", reason="itemized_deductions")
            reply = SCOPE_REFUSAL + " Itemized deductions are outside this prototype."
            session.messages.append({"role": "assistant", "content": reply})
            return reply
        session.answers["take_standard_deduction"] = True
        return finish_return(session)

    if session.phase == "complete":
        return "The 1040 is ready. Use the download button to get the completed PDF."

    return SCOPE_REFUSAL


def finish_return(session: SessionState) -> str:
    if not session.w2:
        raise ValueError("No W-2 is loaded for this session.")
    answers = session.answer_model()
    taxpayer = Taxpayer.from_w2(session.w2)
    session.trace.add("tool_call", tool="compute_1040", args=answers.model_dump())
    lines = compute_1040_tool(session.w2, answers)
    session.trace.add("tool_result", tool="compute_1040", lines=lines.model_dump(mode="json"))
    session.trace.add("tool_call", tool="fill_1040_pdf", args={"filing_status": lines.filing_status})
    pdf_bytes = fill_1040_pdf_tool(lines, taxpayer)
    session.trace.add("tool_result", tool="fill_1040_pdf", bytes=len(pdf_bytes))

    session.lines = lines
    session.taxpayer = taxpayer
    session.pdf_bytes = pdf_bytes
    session.phase = "complete"

    if lines.l35a_refund:
        result = f"a refund of ${int(lines.l35a_refund):,}"
    else:
        result = f"an amount owed of ${int(lines.l37_amount_owed):,}"
    reply = f"Done. I prepared the 2025 Form 1040 with {result}. Download it below. This is an educational prototype, not tax advice or an e-filed return."
    session.messages.append({"role": "assistant", "content": reply})
    return reply
