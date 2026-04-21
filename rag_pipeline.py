# ==========================================================
# 🤖 NARYAN AI — RAG PIPELINE
#    Retrieval-Augmented Generation core engine
# ==========================================================

import os
import re
import logging
import hashlib
from typing import List, Dict

import groq
from cachetools import LRUCache

from vector_store   import vector_store
from subject_detector import detect_subject

logger = logging.getLogger("NARYAN_AI.rag")

# ── Config ─────────────────────────────────────────────────
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS    = int(os.getenv("MAX_TOKENS", 2000))
TEMPERATURE   = float(os.getenv("TEMPERATURE", 0.6))

if not GROQ_API_KEY:
    logger.warning("⚠️  GROQ_API_KEY not set — add it to your .env file")

_client = groq.Groq(api_key=GROQ_API_KEY)
_cache: LRUCache = LRUCache(maxsize=100)

# ── Intent detection ───────────────────────────────────────
INTENT_PATTERNS = {
    "PYQ":      r"(pyq|previous year|past paper|old question|exam question)",
    "ROADMAP":  r"(roadmap|study plan|schedule|path|guide|week.*plan)",
    "CONCEPT":  r"(what is|explain|define|how does|theory|concept|describe)",
    "PRACTICE": r"(practice|exercise|problem|solve|quiz|question)",
    "SUMMARY":  r"(summary|summarize|brief|overview|tldr|short note)",
    "TEST":     r"(/test|generate test|practice test|mock exam)",
    "STUDY":    r"(/study|study mode|teach me|notes on)",
    "JOKE":     r"(joke|funny|humor|laugh)",
    "BOOST":    r"(motivat|boost|inspire|encourage|sad|tired|stressed)",
}

def detect_intent(text: str) -> str:
    for intent, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, text, re.I):
            return intent
    return "GENERAL"


# ── System prompt ──────────────────────────────────────────
def _build_system_prompt(intent: str, context_chunks: List[dict]) -> str:
    base = (
        "You are NARYAN AI — an elite academic intelligence assistant built for B.Tech students "
        "at CV Raman Global University, India.\n"
        "You are knowledgeable, encouraging, and structured. Always format answers with "
        "clear headings, bullet points, or numbered steps when helpful.\n"
        "Never fabricate facts. If you don't know something, say so honestly.\n"
        "Reference the provided knowledge base context when relevant."
    )

    intent_hints = {
        "PYQ": (
            "\n\nYou are retrieving PREVIOUS YEAR QUESTIONS (PYQs). "
            "List questions exactly as found in the knowledge base, grouped by year if available. "
            "Add a brief hint or solution approach for each question."
        ),
        "ROADMAP": (
            "\n\nProvide a structured WEEK-BY-WEEK study roadmap. "
            "Include topics, recommended resources, and daily time allocation."
        ),
        "CONCEPT": (
            "\n\nExplain the concept clearly: definition → formula → intuition → real-world example → common exam traps."
        ),
        "PRACTICE": (
            "\n\nGenerate practice questions with difficulty levels (Easy / Medium / Hard). "
            "Include brief solution hints."
        ),
        "SUMMARY": (
            "\n\nGenerate a concise summary with: Key Points • Important Formulas • Exam Tips."
        ),
        "TEST": (
            "\n\nGenerate a full practice test: 10 MCQs + 5 short-answer questions. "
            "Include answer key at the end."
        ),
        "STUDY": (
            "\n\nEnter STUDY MODE: cover the topic comprehensively — "
            "Concept → Formula → Derivation → Solved Examples → PYQ-style questions."
        ),
        "JOKE":  "\n\nShare one clever, clean engineering or academic joke.",
        "BOOST": "\n\nDeliver a short, powerful motivational message for a student who is struggling.",
        "GENERAL": "",
    }

    context_note = ""
    if context_chunks:
        snippets = "\n\n---\n".join(
            f"[Source: {c['source']} | Subject: {c['subject']} | Type: {c['type']}]\n{c['text']}"
            for c in context_chunks
        )
        context_note = f"\n\n=== KNOWLEDGE BASE CONTEXT ===\n{snippets}\n=== END CONTEXT ==="

    return base + intent_hints.get(intent, "") + context_note


# ── Main generate function ─────────────────────────────────
def generate_response(
    message: str,
    history: List[Dict],
    user_id: int = 0,
    session_id: str = "",
) -> Dict:
    """
    Full RAG pipeline:
      1. Detect intent + subject
      2. Retrieve relevant KB chunks
      3. Build system prompt with context
      4. Call Groq LLM
      5. Cache + return
    """
    cache_key = hashlib.md5(message.encode()).hexdigest()
    if cache_key in _cache:
        logger.info("Cache hit")
        return {**_cache[cache_key], "cached": True}

    intent  = detect_intent(message)
    subject = detect_subject(message)

    # For PYQ queries, prefer PYQ-type chunks
    doc_type_filter = ""
    if intent == "PYQ":
        doc_type_filter = "pyq"

    context_chunks = vector_store.search(
        message,
        k=6,
        subject_filter=subject or "",
    )

    # If PYQ intent, prioritise pyq-type chunks
    if intent == "PYQ":
        pyq_chunks  = [c for c in context_chunks if c.get("type") == "pyq"]
        other_chunks = [c for c in context_chunks if c.get("type") != "pyq"]
        context_chunks = (pyq_chunks + other_chunks)[:6]

    system_prompt = _build_system_prompt(intent, context_chunks)
    messages = [{"role": "system", "content": system_prompt}]

    # Add recent conversation history (last 10 turns)
    for turn in history[-10:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    messages.append({"role": "user", "content": message})

    try:
        resp = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        reply = resp.choices[0].message.content
    except groq.APIConnectionError:
        raise RuntimeError("Cannot connect to Groq API. Check your internet connection.")
    except groq.AuthenticationError:
        raise RuntimeError("Invalid GROQ_API_KEY. Please update your .env file.")
    except groq.RateLimitError:
        raise RuntimeError("Groq rate limit reached. Please wait a moment and try again.")
    except groq.APIStatusError as e:
        raise RuntimeError(f"Groq API error {e.status_code}: {e.message}")

    result = {
        "reply":   reply,
        "intent":  intent,
        "subject": subject or "general",
        "model":   GROQ_MODEL,
        "cached":  False,
        "sources": [
            {"source": c["source"], "subject": c["subject"], "type": c["type"]}
            for c in context_chunks[:3]
        ],
    }
    _cache[cache_key] = result
    return result
