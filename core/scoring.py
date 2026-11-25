"""Scores and feedback for one answer — formulas only, no AI.

grammar      = 10 - 0.8 x (grammar errors per 100 words)
naturalness  = 10 - 0.9 x (collocation / word-choice / structure issues per 100 words) - small style penalties
vocabulary   = 2 + 4 x (share of advanced words / 0.25, capped) + 2 x (lexical variety) + 2 x (passage words reused, up to 3)
content      = length vs. target + number of sentences + linking words + opinion markers + overlap with the passage topic
overall      = 0.3 grammar + 0.25 vocabulary + 0.25 naturalness + 0.2 content
"""
import re

from .grammar import check
from .questions import PHRASE_BANK
from .textutil import words, sentences, is_common, lemma, keywords

CONNECTORS = ["because", "however", "therefore", "although", "moreover", "furthermore", "in addition", "on the other hand",
              "as a result", "for example", "for instance", "while", "whereas", "nevertheless", "that said",
              "consequently", "in contrast", "meanwhile", "since", "so that", "even though", "unless", "overall"]
OPINION = ["i think", "i believe", "in my view", "in my opinion", "i'd argue", "i would argue", "it seems",
           "personally", "i feel", "the way i see it", "i'm inclined", "i expect", "i doubt", "i suspect",
           "i'm convinced", "to me,", "my concern is", "i worry"]
EMOTION = ["feel", "felt", "angry", "sad", "happy", "worried", "relieved", "frustrated", "shocked", "surprised",
           "upset", "anxious", "hopeful", "disappointed", "excited", "scared", "concerned", "heartbroken",
           "furious", "proud", "embarrassed", "taken aback", "devastated"]

TIPS = {
    "agreement": "주어가 3인칭 단수(he, she, it, the company)이면 현재형 동사에 -s를 붙였는지 마지막에 한 번 더 점검하세요.",
    "article": "a/an은 철자가 아니라 첫 소리로 정합니다. an hour, a university, an MBA.",
    "preposition": "discuss, mention, contact, reach, attend, marry는 전치사 없이 바로 목적어를 씁니다. 자주 틀리는 동사만 따로 외워 두세요.",
    "tense": "시간 표현(yesterday, last week, since, for)을 먼저 보고 시제를 맞추세요. 과거 사건은 과거형, 지금까지 이어지면 현재완료.",
    "collocation": "단어는 짝으로 외우세요: make a mistake, do homework, heavy rain, high price.",
    "word_choice": "한국어를 그대로 옮긴 표현(콩글리시)을 조심하세요. 막히면 '써 볼 표현' 문형을 그대로 빌려 쓰세요.",
    "structure": "긴 문장은 둘로 나누고, 이유는 because, 대조는 however/although 하나만 써서 연결하세요.",
    "spelling": "자주 틀리는 철자는 단어장에 따로 적어 두고, 제출 전에 한 번 소리 내어 읽어 보세요.",
    "punctuation": "쉼표·마침표 뒤에 한 칸 띄우고, 문장 끝에는 마침표를 찍으세요.",
    "capitalization": "문장 첫 글자와 I는 항상 대문자입니다.",
    "style": "very + 형용사 대신 한 단어(crucial, furious, delighted)를 쓰면 훨씬 세련돼 보입니다.",
    "repetition": "쓰고 나서 소리 내어 읽어 보면 반복된 단어를 쉽게 찾을 수 있습니다.",
    "grammar": "be동사(am/is/are)와 일반동사를 한 자리에 같이 쓰지 않았는지, 비교급·최상급에 more/most를 겹쳐 쓰지 않았는지 확인하세요.",
    "awkward": "같은 뜻을 두 번 말하지 않았는지 보세요. In my opinion을 썼다면 I think는 빼도 됩니다.",
}


def clamp(x, lo=1.0, hi=10.0):
    return max(lo, min(hi, x))


def assess(text, passage, question, mode="typed", config=None, settings=None):
    config = config or {}
    settings = settings or {}
    res = check(text, config.get("checker", {}), known_words=set(w.lower() for w in words(passage.get("text", ""))))
    issues = res["issues"]
    if mode == "voice":  # speech recognition decides capitals and punctuation, not the learner
        issues = [i for i in issues if i["type"] not in ("punctuation", "capitalization")]

    toks = words(text)
    n = max(1, len(toks))
    sents = sentences(text)
    per100 = lambda k: k * 100.0 / n

    g_err = sum(1 for i in issues if i["category"] in ("grammar",))
    mech = sum(1 for i in issues if i["category"] == "mechanics")
    nat_err = sum(1 for i in issues if i["category"] == "naturalness")
    style = sum(1 for i in issues if i["category"] == "style")

    grammar = clamp(10 - 0.8 * per100(g_err) - 0.15 * per100(mech))
    naturalness = clamp(10 - 0.9 * per100(nat_err) - 0.4 * min(style, 4))

    lw = [t.lower() for t in toks]
    content_words = [w for w in lw if len(w) > 2]
    adv = [w for w in content_words if not is_common(w)]
    adv_ratio = len(adv) / max(1, len(content_words))
    window = lw[:60]
    ttr = len(set(window)) / max(1, len(window))
    passage_terms = {lemma(w) for w in keywords(passage.get("text", "")) if not is_common(w)}
    reused = sorted({w for w in adv if lemma(w) in passage_terms})
    vocabulary = clamp(2 + 4 * min(1, adv_ratio / 0.25) + 2 * min(1, ttr / 0.75) + 2 * min(1, len(reused) / 3))

    target = {"short": 50, "medium": 70, "long": 100}.get(settings.get("answer_target", "medium"), 70)
    low = text.lower()
    conn = sorted({c for c in CONNECTORS if re.search(r"\b" + re.escape(c) + r"\b", low)})
    opin = sorted({o for o in OPINION if o in low})
    emo = sorted({e for e in EMOTION if re.search(r"\b" + re.escape(e) + r"\b", low)})
    topic = {lemma(w) for w in keywords(passage.get("title", "") + " " + passage.get("text", ""))}
    overlap = len({lemma(w) for w in keywords(text)} & topic)
    content = clamp(2 + 3 * min(1, len(toks) / target) + 1.5 * min(1, len(sents) / 3) + 1.5 * min(1, len(conn) / 2)
                    + 1 * (1 if (opin or emo) else 0) + 1 * min(1, overlap / 3))

    overall = round(0.3 * grammar + 0.25 * vocabulary + 0.25 * naturalness + 0.2 * content, 1)
    avg_len = len(toks) / max(1, len(sents))
    if overall >= 8.5 and adv_ratio >= 0.2 and avg_len >= 14:
        cefr = "C1"
    elif overall >= 7 and adv_ratio >= 0.12:
        cefr = "B2"
    elif overall >= 5:
        cefr = "B1"
    else:
        cefr = "A2"

    # summary in Korean from fixed sentences
    parts = {"문법": grammar, "어휘": vocabulary, "자연스러움": naturalness, "내용 구성": content}
    best = max(parts, key=parts.get)
    worst = min(parts, key=parts.get)
    real = [i for i in issues if i["category"] != "style"]
    summary = [f"{len(toks)}단어, {len(sents)}문장으로 답했어요. 가장 좋은 영역은 {best}({parts[best]:.1f}점)입니다."]
    if real:
        top_types = {}
        for i in real:
            if i["category"] != "mechanics" or all(x["category"] == "mechanics" for x in real):
                top_types[i["type_ko"]] = top_types.get(i["type_ko"], 0) + 1
        tt = sorted(top_types.items(), key=lambda kv: -kv[1])[:2]
        summary.append("고칠 부분 " + str(len(real)) + "건 중 " + ", ".join(f"{k} {v}건" for k, v in tt) + "이 가장 눈에 띄어요.")
    else:
        summary.append("규칙 검사에서 걸린 오류가 없습니다.")
    if len(toks) < target * 0.6:
        summary.append(f"분량이 짧은 편이에요. 이유나 예시를 한두 문장 더해 {target}단어 정도를 목표로 해 보세요.")
    elif not conn:
        summary.append("because, however 같은 연결어를 넣으면 논리 흐름이 더 분명해집니다.")
    if reused:
        summary.append("지문의 단어(" + ", ".join(reused[:4]) + ")를 활용한 점이 좋아요.")
    summary.append(f"보완할 영역: {worst}.")

    # expressions to try: from the phrase bank for this question type, skipping ones already used
    kind = question.get("type", "opinion")
    bank = [p for p in PHRASE_BANK.get(kind, []) if p[0].split(" …")[0].lower().rstrip(",. ") not in low][:3]
    if not emo and kind != "emotion":
        bank += PHRASE_BANK["emotion"][:1]
    if not conn:
        bank.append(("However, … / As a result, …", "하지만 / 그 결과"))
    unused_vocab = [v for v in passage.get("vocab", []) if lemma(v["term"].split()[0]) not in {lemma(w) for w in lw}][:3]

    counts = {}
    for i in real:
        counts[i["type"]] = counts.get(i["type"], 0) + 1
    major = {k: v for k, v in counts.items() if k not in ("capitalization", "punctuation")}
    counts = major or counts  # mechanics only decide the tip when nothing else is wrong
    if counts:
        tip = TIPS.get(max(counts, key=counts.get), "")
    elif len(toks) < target:
        tip = "오류가 없으니 이번엔 분량을 늘려 보세요. 근거 하나와 구체적인 예시 하나를 더하면 좋습니다."
    else:
        tip = "관계대명사(which, who)나 분사구문으로 두 문장을 하나로 합치는 연습을 해 보세요. 문장이 한층 고급스러워집니다."

    return {
        "scores": {"grammar": round(grammar, 1), "vocabulary": round(vocabulary, 1),
                   "naturalness": round(naturalness, 1), "content": round(content, 1)},
        "overall": overall, "cefr": cefr + " (추정)",
        "summary_ko": " ".join(summary),
        "corrections": [{k: i[k] for k in ("original", "corrected", "type", "type_ko", "category", "explanation_ko", "autofix")}
                        for i in issues],
        "improved": res["corrected"],
        "polished": res["polished"] if res["polished"] != res["corrected"] else "",
        "better_expressions": [{"expression": e, "meaning_ko": k} for e, k in bank[:5]],
        "passage_words_to_try": [{"term": v["term"], "ko": v.get("ko", "")} for v in unused_vocab],
        "stats": {"words": len(toks), "sentences": len(sents), "advanced_ratio": round(adv_ratio, 3),
                  "connectors": conn, "opinion_markers": opin, "emotion_words": emo, "reused_passage_words": reused},
        "tip_ko": tip,
        "method": "규칙 기반 검사 (AI 미사용)" + (" + LanguageTool" if config.get("checker", {}).get("languagetool", {}).get("enabled") else ""),
    }
