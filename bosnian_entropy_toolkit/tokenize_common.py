#!/usr/bin/env python3
"""Zajednička tokenizacija — IDENTIČNA ent.py (words mode), da bi sve skripte
koje čitaju sirovi tekst davale iste tokene kao glavni pipeline."""
import gzip
import re
from pathlib import Path

WORD_RE = re.compile(r"[A-Za-zÀ-ž0-9]+(?:[-’'][A-Za-zÀ-ž0-9]+)*")


def tokenize_words(line: str):
    return WORD_RE.findall(line)


def open_text(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return open(path, "r", encoding="utf-8", errors="ignore")


def is_letter(ch: str) -> bool:
    """Slovo u smislu Unicode kategorije L* (uključuje č ć đ š ž)."""
    return len(ch) == 1 and ch.isalpha()
