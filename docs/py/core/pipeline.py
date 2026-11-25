"""Shared steps used by both the local app (app.py) and the website builder (build_site.py).
No network and no database here, so this module also runs inside the browser (Pyodide)."""
import datetime as dt
import json

from . import rank, digest, vocab, questions

DEFAULT_SETTINGS = {"passages": 5, "questions": 2, "length": "medium", "answer_target": "medium",
                    "voice_input": True, "tts_rate": 1.0}
LENGTH_WORDS = {"short": 120, "medium": 170, "long": 240}


def dedupe(items):
    """The same article often appears in two feeds of one outlet."""
    seen, out = set(), []
    for it in items:
        key = (it["outlet"], it["title"].lower())
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def make_passages(day, settings, user_g=None):
    n, m = int(settings["passages"]), int(settings["questions"])
    length = LENGTH_WORDS.get(settings.get("length", "medium"), 170)
    user_g = user_g or {}
    # go down the ranking; a story whose feeds give too little text for a passage is skipped
    # (while enough other stories remain), so every passage is long enough to study
    built = [(s, digest.build_passage(s, length)) for s in day["stories"][:max(n * 5, 25)]]
    enough = [b for b in built if len(b[1]["text"].split()) >= min(50, length * 0.4)]
    chosen = enough[:n] if len(enough) >= n else (enough + [b for b in built if b not in enough])[:n]
    chosen.sort(key=lambda b: b[0]["rank"])
    out = []
    for s, p in chosen:
        v = vocab.extract([(s["id"], p["text"])], user_g, max_items=6)
        out.append({"story_id": s["id"], "title": s["title"], "category": s["category"], "outlets": s["outlets"],
                    "rank": s["rank"], "text": p["text"], "sources": p["sources"], "short": p["short"],
                    "links": [{"outlet": a["outlet"], "url": a["link"]} for a in s["articles"][:4] if a["link"]],
                    "vocab": v, "questions": questions.make_questions(s, m, f"{day['date']}-{s['id']}")})
    day["passages"] = out
    docs = [(p["story_id"], p["text"]) for p in out]
    if day.get("digest"):
        docs.append(("digest", " ".join(pp["text"] for sec in day["digest"]["sections"] for pp in sec["paragraphs"])))
    day["vocab"] = vocab.extract(docs, user_g, max_items=25)
    day["settings_used"] = {k: settings[k] for k in ("passages", "questions", "length")}
    return day


def build_day_data(items, date, config, settings, now=None, user_g=None, offline=False):
    items = dedupe(items)
    stories = rank.rank(items, config, now=now)
    day = {"date": date, "created_at": dt.datetime.now().isoformat(timespec="seconds"),
           "n_items": len(items), "outlets": sorted({i["outlet"] for i in items}),
           "stories": stories[:40], "offline": offline}
    day["digest"] = digest.build_digest(stories, date, config)
    return make_passages(day, settings, user_g)


def lite_stories(day, n=15):
    return [{k: s[k] for k in ("id", "rank", "title", "category", "outlets", "n_articles", "score", "score_parts", "terms")}
            | {"links": [{"outlet": a["outlet"], "url": a["link"]} for a in s["articles"][:5]]}
            for s in day["stories"][:n]]


# ---- JSON-in / JSON-out helpers for the browser (Pyodide) ----
def js_make_passages(day_json, settings_json, user_g_json="{}"):
    day = json.loads(day_json)
    day = make_passages(day, {**DEFAULT_SETTINGS, **json.loads(settings_json)}, json.loads(user_g_json))
    return json.dumps({"passages": day["passages"], "vocab": day["vocab"], "settings_used": day["settings_used"]},
                      ensure_ascii=False)
