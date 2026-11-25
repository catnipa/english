"""Grouping the same story across outlets and ranking stories. Pure statistics, no AI.

Score of a story cluster =
    w_outlets   * (number of different outlets covering it)        <- the main signal: "everyone is reporting it"
  + w_items     * log(1 + number of articles in the cluster)
  + w_prominence* average top-of-feed position bonus (1 / (1 + position))
  + w_recency   * freshness (half-life in hours)
  + w_category  * your category preference weight
"""
import datetime as dt
import math
from collections import Counter

from .textutil import keywords, proper_nouns, tfidf_vectors, cosine, sentences

CATEGORY_WORDS = {
    "Markets": "stock stocks dow nasdaq s&p index shares bond bonds yield yields treasury investor investors rally "
               "sell-off selloff earnings futures oil crude gold bitcoin crypto dollar currency fed rate rates "
               "inflation ipo valuation market markets trader traders wall".split(),
    "Business": "company companies ceo executive deal merger acquisition acquire startup revenue profit sales "
                "layoffs layoff hiring retailer brand bank banks lender automaker airline supply chain tariff "
                "tariffs trade export exports import imports business industry factory".split(),
    "Tech": "ai artificial intelligence chip chips semiconductor nvidia apple google microsoft amazon meta openai "
            "anthropic software app apps data cyber cyberattack hack hackers tech technology robot robots smartphone "
            "iphone cloud".split(),
    "Politics": "president trump biden congress senate house republican republicans democrat democrats election "
                "vote voters campaign governor lawmakers bill administration white supreme court judge ruling "
                "policy minister parliament poll polls".split(),
    "World": "war ukraine russia china israel gaza iran nato un united nations military troops strike missile "
             "border refugees ceasefire talks summit europe asia africa india japan korea pope foreign".split(),
    "Society": "school students health hospital police crash shooting fire storm hurricane weather climate "
               "flood flights airport travel community family families church study research disease vaccine "
               "doctors".split(),
}


def categorize(text, hint=""):
    toks = Counter(w.lower() for w in text.replace(",", " ").split())
    scores = {c: sum(toks[w] for w in ws) for c, ws in CATEGORY_WORDS.items()}
    if hint in scores:
        scores[hint] += 1.5
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else (hint or "World")


def cluster_items(items, threshold=0.28):
    docs = [keywords(it["title"] + " " + it["title"] + " " + it.get("description", "")) for it in items]
    vecs = tfidf_vectors(docs)
    ents = [{e.lower() for e in proper_nouns(it["title"] + ". " + it.get("description", "")) if len(e) > 3}
            for it in items]
    order = sorted(range(len(items)), key=lambda i: items[i]["position"])
    clusters = []  # each: {"members": [idx], "centroid": dict, "ents": set}
    for i in order:
        best, best_sim = None, 0.0
        for c in clusters:
            sim = cosine(vecs[i], c["centroid"])
            shared = len(ents[i] & c["ents"])
            if shared >= 2:
                sim += 0.15
            if sim > best_sim:
                best, best_sim = c, sim
        if best is not None and best_sim >= threshold:
            best["members"].append(i)
            n = len(best["members"])
            cen = dict(best["centroid"])
            for t, x in vecs[i].items():
                cen[t] = cen.get(t, 0.0) * (n - 1) / n + x / n
            for t in list(cen):
                if t not in vecs[i]:
                    cen[t] = cen[t] * (n - 1) / n
            best["centroid"] = cen
            best["ents"] |= ents[i]
        else:
            clusters.append({"members": [i], "centroid": dict(vecs[i]), "ents": set(ents[i])})
    # second pass: headline-only items (e.g. Google News) join the cluster whose headlines share 2+ key words
    title_kw = [set(keywords(it["title"])) for it in items]
    for c in [c for c in clusters if len(c["members"]) == 1 and not items[c["members"][0]].get("description")]:
        i = c["members"][0]
        best, best_shared = None, 1
        for other in clusters:
            if other is c or not other["members"]:
                continue
            shared = max(len(title_kw[i] & title_kw[j]) for j in other["members"])
            if shared > best_shared:
                best, best_shared = other, shared
        if best is not None:
            best["members"].append(i)
            c["members"] = []
    return [c for c in clusters if c["members"]]


def rank(items, config, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    max_age = config.get("max_age_hours", 36)
    fresh = []
    for it in items:
        try:
            age = (now - dt.datetime.fromisoformat(it["published"])).total_seconds() / 3600
        except ValueError:
            age = 0
        if age <= max_age:
            it["age_hours"] = max(0.0, age)
            fresh.append(it)
    if not fresh:
        fresh = items
        for it in fresh:
            it.setdefault("age_hours", 0.0)

    w = config.get("weights", {})
    w_out, w_items = w.get("outlets", 3.0), w.get("items", 1.0)
    w_prom, w_rec, w_cat = w.get("prominence", 2.0), w.get("recency", 1.5), w.get("category", 1.0)
    half_life = config.get("recency_half_life_hours", 12)
    cat_pref = config.get("category_preference", {})

    stories = []
    for c in cluster_items(fresh, config.get("cluster_threshold", 0.28)):
        mem = [fresh[i] for i in c["members"]]
        outlets = sorted({m["outlet"] for m in mem})
        prominence = sum(1 / (1 + m["position"]) for m in mem) / len(mem)
        recency = sum(0.5 ** (m["age_hours"] / half_life) for m in mem) / len(mem)
        # representative: the member with the longest text, preferring top-of-feed
        rep = max(mem, key=lambda m: (len(m.get("body") or m.get("description") or ""), -m["position"]))
        head = min(mem, key=lambda m: (m["position"], -len(m["title"])))
        all_text = " ".join(m["title"] + ". " + (m.get("description") or "") for m in mem)
        category = categorize(all_text, Counter(m["feed_category"] for m in mem).most_common(1)[0][0])
        score = (w_out * len(outlets) + w_items * math.log(1 + len(mem)) + w_prom * prominence
                 + w_rec * recency + w_cat * cat_pref.get(category, 0))
        top_terms = [t for t, _ in sorted(c["centroid"].items(), key=lambda kv: -kv[1])[:6]]
        stories.append({
            "title": head["title"],
            "category": category,
            "outlets": outlets,
            "n_articles": len(mem),
            "score": round(score, 3),
            "score_parts": {"outlets": len(outlets), "articles": len(mem), "prominence": round(prominence, 3),
                            "recency": round(recency, 3), "category_pref": cat_pref.get(category, 0)},
            "terms": top_terms,
            "entities": sorted(c["ents"])[:8],
            "articles": [{"outlet": m["outlet"], "title": m["title"], "link": m["link"],
                          "description": m.get("description", ""), "body": m.get("body", ""),
                          "published": m["published"]} for m in sorted(mem, key=lambda m: m["position"])],
            "rep_text": rep.get("body") or rep.get("description") or rep["title"],
        })
    stories.sort(key=lambda s: -s["score"])
    for i, s in enumerate(stories):
        s["rank"] = i + 1
        s["id"] = f"s{i + 1}"
    return stories


def story_sentences(story):
    """All usable sentences of a story with their outlet, deduplicated."""
    seen, out = set(), []
    for a in story["articles"]:
        for s in sentences((a.get("body") or "") + " " + (a.get("description") or "")):
            key = " ".join(keywords(s))[:120]
            if len(s.split()) < 8 or key in seen:
                continue
            seen.add(key)
            out.append((a["outlet"], s))
    return out
