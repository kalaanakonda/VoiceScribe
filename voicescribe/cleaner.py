"""Basic text cleanup — runs instantly, no API needed."""

import re

FILLER = re.compile(
    r"\b(um|uh|uh huh|like|you know|basically|literally|so yeah|i mean|right|okay so)\b",
    re.IGNORECASE,
)


def clean(text: str) -> str:
    if not text:
        return ""
    text = FILLER.sub("", text)
    text = re.sub(r"\s{2,}", " ", text)           # collapse whitespace
    text = re.sub(r"([.!?])\s*\1+", r"\1", text)  # dedupe punctuation
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)   # space before punctuation
    text = text.strip()
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    return text
