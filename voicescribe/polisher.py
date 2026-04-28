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

# ── Developer mode ──────────────────────────────────────────────────────────
# Same strict cleaning, plus: convert spoken file/syntax/jargon into the
# proper written form (app.py instead of "app dot pi", useState instead of
# "use state", JSON instead of "jay-son").
DEV_SYSTEM_PROMPT = """You clean voice transcripts spoken by a software developer. Apply ALL the regular cleaning rules (remove fillers, fix punctuation, never paraphrase), AND apply these developer-specific transforms:

FILE TAGGING:
- "app dot py" / "app dot pie" → app.py
- "dashboard dot HTML" → dashboard.html
- "package dot json" / "package dot jay son" → package.json
- "dot env" → .env
- "tsconfig dot json" → tsconfig.json
- Any "<word> dot <ext>" pattern with a known extension (py, js, ts, jsx, tsx, html, css, json, md, sh, rb, go, rs, yaml, yml, toml) → join as filename with the dot.

SYNTAX AWARENESS:
- "use state" → useState
- "use effect" → useEffect
- "kebab case" stays as written; convert "use-state" stays as "useState" if it's the React hook
- "camel case my variable" → myVariable (only if context clearly asks for code)
- Code identifiers stay verbatim if already correct.
- Wrap obvious code/commands in backticks: `git push`, `npm install`, `kubectl apply`, `useState`, `app.py`, `localhost:3000`, etc.

DEV JARGON — keep these acronyms and brand names exactly:
API, REST, GraphQL, JSON, YAML, HTML, CSS, JS, TS, TSX, JSX, SQL, NoSQL, MongoDB, PostgreSQL, Redis, Docker, Kubernetes, k8s, AWS, GCP, S3, EC2, CI, CD, CI/CD, npm, pnpm, yarn, git, GitHub, GitLab, PR, MR, IDE, VS Code, IntelliJ, Vim, async, await, Promise, fetch, XHR, OAuth, JWT, CORS, TLS, SSL, HTTPS, IP, DNS, CDN, SaaS, PaaS, UI, UX, CLI, GUI, DOM, SSR, SSG, ISR, RSC, Next.js, React, Vue, Svelte, Angular, Node, Deno, Bun, Python, Ruby, Rust, Go, Java, Kotlin, Swift, ObjC, Whisper, Ollama, llama, GPT, LLM, RAG, MCP.

ABSOLUTE RULES (same as base mode):
- Output the SAME words as the input, in the SAME order. Do NOT rephrase.
- Remove ONLY: um, uh, hmm, er, ah, like, you know, I mean, basically, sort of, kind of.
- KEEP modal verbs (should, would, could, might, may) and qualifiers (just, really, maybe, probably).
- NEVER add explanations. NEVER respond conversationally.
- Output ONLY the cleaned transcript. Nothing else."""

DEV_FEW_SHOT = [
    ("uh let me edit the index dot tsx file real quick",
     "Let me edit the `index.tsx` file real quick."),
    ("yeah I'm gonna use use state for that and then we can call set count",
     "Yeah, I'm going to use `useState` for that and then we can call `setCount`."),
    ("um you should run npm install and then start the server",
     "You should run `npm install` and then start the server."),
    ("the api keeps returning a 500 error from the postgres database",
     "The API keeps returning a 500 error from the PostgreSQL database."),
    ("so the package dot json has a typo in the dependencies field",
     "So the `package.json` has a typo in the dependencies field."),
    ("can you push this branch to origin and open a pull request",
     "Can you push this branch to origin and open a pull request?"),
]

# Whisper initial-prompt boost — biases speech recognition toward common
# dev terms so they come out as the right tokens (e.g. "useState", not
# "use state"; "kubectl", not "cube control").
DEV_VOCAB = (
    "useState, useEffect, useMemo, useCallback, useRef, useContext, "
    "PostgreSQL, MongoDB, Redis, Docker, Kubernetes, kubectl, "
    "Next.js, React, TypeScript, JavaScript, Python, GraphQL, REST, "
    "JSON, YAML, npm, pnpm, yarn, git, GitHub, OAuth, JWT, async, await, "
    "Whisper, Ollama, MCP, RAG, LLM, "
    "app.py, package.json, tsconfig.json, .env, dashboard.html, "
    "localhost, kebab-case, camelCase, snake_case."
)

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


# Auto-detect when the speaker is talking about code, files, or dev tools.
# When any of these markers fire, we route through the developer-aware
# prompt; otherwise we use the plain-prose prompt.  No toggle needed.
_DEV_MARKERS = re.compile(
    r"\b("
    r"\w+\s+dot\s+(py|js|ts|jsx|tsx|html|css|json|md|sh|rb|go|rs|yaml|yml|toml|env)"
    r"|use\s+(state|effect|memo|callback|ref|context|reducer)"
    r"|api|json|yaml|html|css|sql|kubectl|docker|kubernetes"
    r"|git\s+(push|pull|commit|merge|rebase|clone|checkout|branch|status)"
    r"|npm|pnpm|yarn|deno|bun|cargo|pip|brew"
    r"|postgres(?:ql)?|mongo(?:db)?|redis|mysql|sqlite|supabase|firebase"
    r"|next\s*\.?\s*js|react|vue|svelte|angular|nuxt|remix"
    r"|typescript|javascript|python|golang|rust|kotlin|swift"
    r"|oauth|jwt|cors|tls|ssl|cdn|saas|paas|ide|cli|gui|dom|ssr|ssg|isr|rsc"
    r"|github|gitlab|vercel|netlify|cloudflare|aws|azure|gcp"
    r"|whisper|ollama|gpt|llm|rag|mcp"
    r"|merge\s+conflict|pull\s+request|backend|frontend|fullstack|devops"
    r")\b",
    re.IGNORECASE,
)


def is_dev_context(text: str) -> bool:
    """Heuristic: does this transcript look like a developer talking about code?"""
    return bool(text and _DEV_MARKERS.search(text))


def _build_messages(text: str) -> list:
    """Return the chat-API messages list with system prompt + few-shot.
    Auto-routes to developer prompt when the input mentions code-like things."""
    if is_dev_context(text):
        system = DEV_SYSTEM_PROMPT
        examples = DEV_FEW_SHOT + FEW_SHOT[:2]  # mix in plain-prose examples
    else:
        system = SYSTEM_PROMPT
        examples = FEW_SHOT
    messages = [{"role": "system", "content": system}]
    for raw, clean in examples:
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
    survived the polish.  We also collapse 'word dot ext' patterns into a
    single token so the file-tagging transform doesn't trip the audit."""
    text = re.sub(
        r"\b(\w+)\s+dot\s+(py|js|ts|jsx|tsx|html|css|json|md|sh|rb|go|rs|yaml|yml|toml|env)\b",
        r"\1.\2", text, flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"[^\w\s'.]", " ", text.lower())
    return {w for w in cleaned.split() if w and w not in _FILLERS}


_DEV_NORMALIZE = [
    # Map spoken forms to the canonical code form so the content-word
    # audit doesn't punish legitimate dev transforms.
    (re.compile(r"\buse\s+state\b", re.I), "usestate"),
    (re.compile(r"\buse\s+effect\b", re.I), "useeffect"),
    (re.compile(r"\buse\s+memo\b", re.I), "usememo"),
    (re.compile(r"\buse\s+callback\b", re.I), "usecallback"),
    (re.compile(r"\buse\s+ref\b", re.I), "useref"),
    (re.compile(r"\buse\s+context\b", re.I), "usecontext"),
    (re.compile(r"\bset\s+count\b", re.I), "setcount"),
    (re.compile(r"\bset\s+state\b", re.I), "setstate"),
    (re.compile(r"\bpostgres(?:ql)?\b", re.I), "postgresql"),
    (re.compile(r"\b(\w+)\s+dot\s+(py|js|ts|jsx|tsx|html|css|json|md|sh|rb|go|rs|yaml|yml|toml|env)\b", re.I),
     r"\1.\2"),
]


def _normalize_for_audit(text: str, dev_mode: bool) -> str:
    """Pre-process text so equivalent spoken / code forms compare equal."""
    if dev_mode:
        for pat, repl in _DEV_NORMALIZE:
            text = pat.sub(repl, text)
    return text


def _looks_like_chatbot_drift(output: str, original: str, dev_mode: bool = False) -> bool:
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
    if out_words > in_words * 3 + 5:
        return True
    if in_words >= 12 and out_words < in_words * 0.45:
        return True

    # Content-word check (with dev-aware normalization so transforms like
    # "use state" → "useState" are recognised as the same content).
    norm_in = _normalize_for_audit(original, dev_mode)
    norm_out = _normalize_for_audit(output, dev_mode)
    in_content = _content_words(norm_in)
    out_content = _content_words(norm_out)
    if len(in_content) >= 4:
        missing = in_content - out_content
        # Slightly more permissive in dev mode (transforms shift more words)
        threshold = 0.40 if dev_mode else 0.30
        if len(missing) / len(in_content) > threshold:
            return True

    return False


def polish(text: str, model: str) -> str:
    """Polish a raw transcript via Ollama's chat API.

    Auto-detects dev context — if the input mentions filenames, hooks,
    commands, or other dev markers, the developer-aware prompt kicks in.
    No toggle, no setting.

    Returns:
        - the polished text on success
        - the *original* text if the model drifts into chatbot mode
        - None if Ollama itself fails (caller should fall back to rule-based)
    """
    if not text or not text.strip() or not model:
        return None
    if len(text.split()) < MIN_WORDS_FOR_POLISH:
        return text

    dev_mode = is_dev_context(text)

    payload = json.dumps({
        "model": model,
        "messages": _build_messages(text),
        "stream": False,
        "options": {
            "temperature": 0.0,    # deterministic — no creativity
            "top_p": 0.9,
            "num_predict": 1024,
            # Note: NO repeat_penalty — penalising repetition makes the model
            # avoid restating the user's words, which we want to preserve.
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
    if _looks_like_chatbot_drift(result, text, dev_mode=dev_mode):
        return text

    return result or text
