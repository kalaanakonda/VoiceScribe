"""AI polish — clean up Whisper transcripts via a local LLM (Ollama).

Uses Ollama's /api/chat endpoint with a system prompt + few-shot examples,
which is the canonical way to constrain chat-tuned models like llama3.2:3b.
We also reject "chatbot drift" responses ("I'm ready to help...") and short
inputs that don't have enough content for the model to anchor on.
"""

import json
import re
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434"
TIMEOUT_QUICK = 2
TIMEOUT_GENERATE = 60

# Models we recommend for this task (small, fast, instruction-tuned)
PREFERRED_MODELS = [
    "llama3.2:3b",
    "llama3.2:1b",
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "qwen2.5:0.5b",
    "phi3.5:3.8b",
    "phi3:mini",
    "gemma2:2b",
]

SYSTEM_PROMPT = """You clean voice transcripts. You do TWO things only: remove fillers, and add punctuation.

ABSOLUTE RULES — follow them exactly:
1. Output the SAME words as the input, in the SAME order. Do NOT rephrase.
2. Remove ONLY these filler words: um, uh, hmm, er, ah, like, you know, I mean, basically, sort of, kind of.
3. Collapse stutters: "the the" → "the", "I I think" → "I think".
4. Add capitalization and punctuation (. , ?).
5. KEEP every other word verbatim — including: should, would, could, might, may, will, just, really, maybe, yeah, okay, actually, so, well, hey, anyway, and ALL named things.
6. NEVER replace a word with a synonym. NEVER shorten "what should be" to "what's". NEVER turn "we should do this" into "let's do this".
7. NEVER add explanations. NEVER respond conversationally. NEVER say "I'm ready" or "Sure!" or "Here is".
8. Output ONLY the cleaned transcript. Nothing else."""

# Few-shot exemplars — strict filler removal only, no rephrasing.
FEW_SHOT = [
    ("um what should be the next step",
     "What should be the next step?"),
    ("So like, I was thinking we could maybe ship this thing on Friday you know",
     "So I was thinking we could maybe ship this thing on Friday."),
    ("uh basically the the api is broken and i mean we need to fix it before the demo",
     "The API is broken and we need to fix it before the demo."),
    ("Hey can you um send me the link to the doc",
     "Hey, can you send me the link to the doc?"),
    ("yeah I think we should merge the PR and then deploy it to staging first",
     "Yeah, I think we should merge the PR and then deploy it to staging first."),
    ("hmm okay so what what is happening here this is really weird",
     "Okay, so what is happening here? This is really weird."),
]

# Phrases that signal the model has gone into chatbot mode rather than
# performing the transformation — when output starts with any of these,
# we treat the polish as failed and fall back to the raw transcript.
CHATBOT_PREFIXES = (
    "i'm ready", "i am ready",
    "i'd be happy", "i would be happy",
    "i apologize", "i'm sorry",
    "please provide", "please share",
    "sure!", "of course!",
    "here's the cleaned", "here is the cleaned",
    "the cleaned text", "cleaned transcript",
    "as an ai", "as a transcript",
    "i'll", "i will help",
)

# Minimum word count to bother sending to the LLM.  Short utterances are
# usually mis-interpreted as instructions ("Can you hear me?" → chat reply).
MIN_WORDS_FOR_POLISH = 6


def is_available() -> bool:
    """Returns True if Ollama is reachable on localhost:11434."""
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=TIMEOUT_QUICK) as resp:
            return resp.status == 200
    except Exception:
        return False


def list_models() -> list:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=TIMEOUT_QUICK) as resp:
            data = json.loads(resp.read().decode())
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def suggest_default_model(installed: list) -> str:
    if not installed:
        return None
    for pref in PREFERRED_MODELS:
        for name in installed:
            if name == pref or name.startswith(pref + "-") or name.startswith(pref):
                return name
    return sorted(installed, key=lambda n: len(n))[0]


def _build_messages(text: str) -> list:
    """Return the chat-API messages list with system prompt + few-shot."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for raw, clean in FEW_SHOT:
        messages.append({"role": "user", "content": raw})
        messages.append({"role": "assistant", "content": clean})
    messages.append({"role": "user", "content": text})
    return messages


_FILLERS = {
    "um", "uh", "hmm", "er", "ah", "like", "basically",
    "you", "know", "i", "mean", "sort", "of", "kind",
}


def _content_words(text: str) -> set:
    """Lowercased non-filler words, useful for measuring how much real content
    survived the polish."""
    cleaned = re.sub(r"[^\w\s']", " ", text.lower())
    return {w for w in cleaned.split() if w and w not in _FILLERS}


def _looks_like_chatbot_drift(output: str, original: str) -> bool:
    """Heuristic: did the model respond conversationally, paraphrase, or
    drop important words instead of just cleaning?"""
    if not output:
        return True
    lower = output.lower().lstrip()
    if any(lower.startswith(p) for p in CHATBOT_PREFIXES):
        return True

    in_words = len(original.split())
    out_words = len(output.split())
    if in_words == 0:
        return False
    # Output wildly longer than input → model added preamble
    if out_words > in_words * 3 + 5:
        return True
    # Output dropped half the words → summarizing, not cleaning
    if in_words >= 12 and out_words < in_words * 0.45:
        return True

    # Content-word check: if more than 30% of the input's content words
    # are missing from the output, the model rephrased instead of cleaning.
    in_content = _content_words(original)
    out_content = _content_words(output)
    if len(in_content) >= 4:
        missing = in_content - out_content
        if len(missing) / len(in_content) > 0.30:
            return True

    return False


def polish(text: str, model: str) -> str:
    """Polish a raw transcript via Ollama's chat API.

    Returns:
        - the polished text on success
        - the *original* text if the model drifts into chatbot mode
        - None if Ollama itself fails (caller should fall back to rule-based)
    """
    if not text or not text.strip() or not model:
        return None
    # Don't polish very short utterances — too easy for the model to
    # misinterpret them as instructions.
    if len(text.split()) < MIN_WORDS_FOR_POLISH:
        return text

    payload = json.dumps({
        "model": model,
        "messages": _build_messages(text),
        "stream": False,
        "options": {
            "temperature": 0.0,    # deterministic — no creativity
            "top_p": 0.9,
            "num_predict": 1024,
            "repeat_penalty": 1.05,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_GENERATE) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None

    msg = data.get("message") or {}
    result = (msg.get("content") or "").strip()
    if not result:
        return None

    # Strip wrapping quotes the model sometimes adds
    if (result.startswith('"') and result.endswith('"')) or \
       (result.startswith("'") and result.endswith("'")):
        result = result[1:-1].strip()
    # Strip common prefixes
    result = re.sub(
        r"^(cleaned( text| transcript| version)?|output|result|here(?:'s| is) the cleaned[^:]*):\s*",
        "",
        result,
        flags=re.IGNORECASE,
    ).strip()

    # If the model went into chatbot mode, fall back to the raw transcript
    # so the user gets *something* useful instead of "I'm ready to help...".
    if _looks_like_chatbot_drift(result, text):
        return text

    return result or text
