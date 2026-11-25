"""Vocabulary list from today's passages, without AI.

Rules
- single words: not in the common-word list, at least 4 letters, used in lowercase somewhere
  (so names like "Nvidia" are skipped); score = frequency + length + glossary bonus + spread across stories
- phrases: any multi-word entry of the glossary found in the text, plus two-word collocations
  that appear at least twice
- Korean meaning: from the built-in glossary or your my_glossary.tsv; otherwise a dictionary link
"""
import os
import re
import urllib.parse
from collections import Counter, defaultdict

from .glossary import GLOSSARY
from .textutil import sentences, words, is_common, lemma, STOPWORDS

PHRASAL = {"step down", "crack down", "roll out", "rule out", "ramp up", "scale back", "push back", "back down",
           "shut down", "wind down", "pull out", "carry out", "set up", "take over", "call for", "point out",
           "bring about", "phase out", "drive up", "weigh on", "lay off", "spin off", "sign off", "look into",
           "turn around", "hold off", "play down", "build up", "head off", "fall short", "pick up"}


def load_user_glossary(base_dir):
    path = os.path.join(base_dir, "my_glossary.tsv")
    g = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if "\t" in line and not line.startswith("#"):
                    k, v = line.rstrip("\n").split("\t", 1)
                    g[k.strip().lower()] = v.strip()
    return g


def dict_url(term):
    return "https://en.dict.naver.com/#/search?query=" + urllib.parse.quote(term)


def meaning(term, user_g):
    t = term.lower()
    for cand in (t, lemma(t)):
        if cand in user_g:
            return user_g[cand]
        if cand in GLOSSARY:
            return GLOSSARY[cand]
    return ""


def extract(docs, user_g=None, max_items=20):
    """docs: list of (doc_id, text). Returns ranked list of vocab dicts."""
    user_g = user_g or {}
    count, lower_seen, spread, example = Counter(), set(), defaultdict(set), {}
    phrase_count, phrase_example = Counter(), {}
    multi = [k for k in list(GLOSSARY) + list(user_g) if " " in k] + list(PHRASAL)

    for doc_id, text in docs:
        for sent in sentences(text):
            toks = words(sent)
            low_sent = " " + " ".join(t.lower() for t in toks) + " "
            for t in toks:
                lw = t.lower()
                if t == lw:
                    lower_seen.add(lemma(lw))
                if len(lw) < 4 or not lw.isalpha() and "-" not in lw or is_common(lw):
                    continue
                key = lemma(lw)
                count[key] += 1
                spread[key].add(doc_id)
                example.setdefault(key, sent)
            for m in multi:
                if " " + m + " " in low_sent or re.search(r"\b" + re.escape(m.split()[0]) + r"\w*\s+" +
                                                           re.escape(" ".join(m.split()[1:])) + r"\b", low_sent):
                    phrase_count[m] += 1
                    phrase_example.setdefault(m, sent)
            for a, b in zip(toks, toks[1:]):
                la, lb = a.lower(), b.lower()
                if la in STOPWORDS or lb in STOPWORDS or not (la.isalpha() and lb.isalpha()):
                    continue
                if a[0].isupper() or b[0].isupper():
                    continue
                if is_common(la) and is_common(lb):
                    continue
                phrase_count[la + " " + lb] += 1
                phrase_example.setdefault(la + " " + lb, sent)

    items = []
    for key, c in count.items():
        if key not in lower_seen:  # only ever capitalized -> probably a name
            continue
        ko = meaning(key, user_g)
        score = c + min(len(key), 12) / 4 + (3 if ko else 0) + (len(spread[key]) - 1)
        items.append({"term": key, "kind": "word", "count": c, "ko": ko, "example": example[key],
                      "score": round(score, 2), "dict": dict_url(key)})
    for p, c in phrase_count.items():
        in_g = bool(meaning(p, user_g)) or p in PHRASAL
        if not in_g and c < 2:
            continue
        ko = meaning(p, user_g)
        items.append({"term": p, "kind": "phrase", "count": c, "ko": ko, "example": phrase_example[p],
                      "score": round(c + 4 + (2 if ko else 0), 2), "dict": dict_url(p)})
    items.sort(key=lambda x: -x["score"])
    # drop single words already covered by a chosen phrase
    out, covered = [], set()
    for it in items:
        if it["kind"] == "word" and it["term"] in covered:
            continue
        out.append(it)
        if it["kind"] == "phrase":
            covered.update(lemma(w) for w in it["term"].split())
        if len(out) >= max_items:
            break
    return out
