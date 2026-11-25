"""Daily briefing built WITHOUT AI.

How it works
1. Take the top-ranked stories.
2. Inside each story, rank sentences with TextRank (a graph algorithm: a sentence is important if
   it shares many key words with the other sentences about the same story) and pick 2-3,
   skipping near-duplicates (MMR).
3. Group the stories into sections by category and add fixed, data-driven connecting text
   (how many outlets covered what, which words dominated, what is scheduled next).
The sentences themselves come from the outlets' own RSS summaries / article openings, with the outlet named.
"""
import datetime as dt
import re
from collections import Counter

from .rank import story_sentences
from .textutil import keywords, tfidf_vectors, cosine, truncate_words, word_count, sentences

SECTION_TITLE = {
    "Markets": "Markets & the Economy", "Business": "Business & Industry", "Tech": "Technology",
    "Politics": "Politics & Policy", "World": "World Affairs", "Society": "Society & Everyday Life",
}
SECTION_KO = {"Markets": "시장·경제", "Business": "기업·산업", "Tech": "기술", "Politics": "정치·정책",
              "World": "국제", "Society": "사회·생활"}
OPENERS = {
    "Markets": ["On the markets front,", "For investors,", "In the markets,"],
    "Business": ["In the corporate world,", "On the business side,", "Among companies,"],
    "Tech": ["In technology,", "On the tech front,", "In Silicon Valley and beyond,"],
    "Politics": ["In Washington and beyond,", "On the political front,", "In politics,"],
    "World": ["Overseas,", "Around the world,", "On the international stage,"],
    "Society": ["Closer to home,", "In other news,", "Away from politics and markets,"],
}
FUTURE = re.compile(r"\b(will|next week|next month|tomorrow|expected to|plans to|is set to|are set to|"
                    r"scheduled|later this|could|deadline|upcoming|due to)\b", re.I)


def textrank(sent_list, iterations=30, d=0.85):
    if not sent_list:
        return []
    vecs = tfidf_vectors([keywords(s) for s in sent_list])
    n = len(sent_list)
    sim = [[cosine(vecs[i], vecs[j]) if i != j else 0.0 for j in range(n)] for i in range(n)]
    out_sum = [sum(row) or 1.0 for row in sim]
    score = [1.0] * n
    for _ in range(iterations):
        score = [(1 - d) + d * sum(sim[j][i] / out_sum[j] * score[j] for j in range(n)) for i in range(n)]
    # earlier sentences in news are usually more important (inverted pyramid)
    return [s + 0.25 / (1 + i) for i, s in enumerate(score)], vecs


def pick_sentences(story, k=3, max_words=95):
    pairs = story_sentences(story)
    if not pairs:
        return [(story["outlets"][0], story["title"] + ".")]
    texts = [s for _, s in pairs]
    scores, vecs = textrank(texts)
    chosen = []
    for i in sorted(range(len(texts)), key=lambda i: -scores[i]):
        if any(cosine(vecs[i], vecs[j]) > 0.35 for j in chosen):
            continue
        if sum(word_count(texts[j]) for j in chosen) + word_count(texts[i]) > max_words and chosen:
            continue
        chosen.append(i)
        if len(chosen) >= k:
            break
    chosen.sort()
    return [pairs[i] for i in chosen]


def build_digest(stories, date_str, config):
    top = stories[: config.get("digest_stories", 8)]
    if not top:
        return None
    outlets_all = sorted({o for s in stories for o in s["outlets"]})
    d = dt.date.fromisoformat(date_str)
    day_label = d.strftime("%A, %B ") + str(d.day)

    # overview paragraph (data-driven, fixed wording)
    t1 = top[0]
    overview = [f"{len(stories)} distinct stories ran across {len(outlets_all)} major outlets in the latest news cycle."]
    overview.append(f"The most widely covered was “{t1['title']}”, reported by {len(t1['outlets'])} "
                    f"outlet{'s' if len(t1['outlets']) != 1 else ''} ({', '.join(t1['outlets'])}).")
    if len(top) >= 3:
        overview.append(f"It was followed by “{top[1]['title']}” and “{top[2]['title']}”.")
    cats = Counter(s["category"] for s in top)
    main_cat, main_n = cats.most_common(1)[0]
    overview.append(f"{SECTION_TITLE.get(main_cat, main_cat)} dominated the agenda, accounting for "
                    f"{main_n} of the top {len(top)} stories.")
    term_counts = Counter(t for s in top for t in s["terms"][:4])
    hot = [t for t, _ in term_counts.most_common(6)]
    if hot:
        overview.append("Words that kept coming up: " + ", ".join(hot) + ".")

    sections, order = [], []
    for s in top:
        if s["category"] not in order:
            order.append(s["category"])
    for ci, cat in enumerate(order):
        paras = []
        for si, s in enumerate([x for x in top if x["category"] == cat]):
            picked = pick_sentences(s, k=config.get("digest_sentences_per_story", 3))
            opener = OPENERS.get(cat, ["Meanwhile,"])[(ci + si) % 3] if si == 0 else "Meanwhile,"
            first_outlet, first = picked[0]
            body = [f"{opener} {first_outlet} reports: {first}"] + [s2 for _, s2 in picked[1:]]
            paras.append({"story_id": s["id"], "title": s["title"], "text": " ".join(body),
                          "outlets": s["outlets"], "n_articles": s["n_articles"]})
        sections.append({"category": cat, "subhead": SECTION_TITLE.get(cat, cat), "paragraphs": paras})

    watch = []
    for s in top:
        for outlet, sent in story_sentences(s):
            if FUTURE.search(sent) and 8 <= len(sent.split()) <= 40:
                watch.append(f"{sent} ({outlet})")
                break
        if len(watch) >= 3:
            break

    themes_ko = []
    for cat in order:
        firsts = [s for s in top if s["category"] == cat]
        themes_ko.append(f"{SECTION_KO.get(cat, cat)} {len(firsts)}건 · 대표 기사: {firsts[0]['title']}")

    return {
        "headline": "Today's World Briefing: " + t1["title"],
        "dek": f"What {len(outlets_all)} major outlets covered for {day_label}, ranked by how widely each story was reported.",
        "overview": " ".join(overview),
        "sections": sections,
        "watch_next": watch,
        "themes_ko": themes_ko,
        "method_note": "이 브리핑은 AI가 쓴 글이 아니라, 각 언론사 기사 요약문에서 TextRank 알고리즘으로 핵심 문장을 골라 "
                       "분야별로 엮고 고정 문장 틀로 연결한 것입니다.",
    }


def build_passage(story, length_words):
    """A reading passage for one story: article opening if we have it, otherwise the best sentences."""
    body = ""
    for a in story["articles"]:
        if a.get("body") and word_count(a["body"]) >= length_words * 0.7:
            body = a["body"]
            src = a["outlet"]
            break
    if body:
        text = truncate_words(body.replace("\n\n", " "), length_words)
        sources = [src]
    else:
        picked = pick_sentences(story, k=8, max_words=length_words)
        text = " ".join(s for _, s in picked)
        sources = sorted({o for o, _ in picked})
    if word_count(text) < 25:  # very thin feeds: fall back to all descriptions
        text = " ".join(dict.fromkeys(a["description"] for a in story["articles"] if a["description"])) or story["title"]
    return {"text": text, "sources": sources, "short": word_count(text) < length_words * 0.5}
