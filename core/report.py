"""Learning report from your own history — counting and fixed rules, no AI."""
import datetime as dt
from collections import Counter, defaultdict

ADVICE = {
    "agreement": ("주어-동사 수 일치", "주어를 찾고 동사에 동그라미 치는 습관을 들이세요. he/she/it·the company·everyone 뒤 현재형은 -s, people·they 뒤는 복수형.",
                  "매일 답변을 제출하기 전에 문장마다 주어와 동사만 소리 내어 읽어 보기"),
    "article": ("관사 a/an/the", "처음 언급하는 셀 수 있는 단수 명사에는 a/an, 다시 언급하거나 하나뿐인 것에는 the. a/an은 발음 기준.",
                "지문 하나를 골라 a/an/the가 붙은 명사 10개를 표시하고 이유를 적어 보기"),
    "preposition": ("불필요하거나 틀린 전치사", "discuss/mention/contact/reach/attend/marry/enter는 전치사 없이 씁니다. 기간은 for, 시작점은 since.",
                    "'전치사 없는 동사' 7개로 예문을 하나씩 만들어 소리 내어 읽기"),
    "tense": ("시제", "과거 시점 표현이 있으면 과거형, 지금까지 이어지면 현재완료(have been). if절은 미래라도 현재형.",
              "어제 있었던 일을 과거형으로만 5문장 쓰기"),
    "collocation": ("단어 궁합(연어)", "make a mistake, do homework, heavy rain, high price처럼 단어를 짝으로 기억하세요.",
                    "브리핑의 '자주 나온 표현'을 단어장에 추가하고 짝 표현으로 복습하기"),
    "word_choice": ("단어 선택·콩글리시", "interested/interesting, bored/boring 같은 감정 형용사와 콩글리시를 주의하세요.",
                    "감정 형용사 -ed/-ing 짝 10개로 예문 만들기"),
    "structure": ("문장 구조", "한 문장에는 한 가지 생각. 35단어가 넘으면 나누고, although와 but은 같이 쓰지 않습니다.",
                  "긴 답변 하나를 골라 3~4개의 짧은 문장으로 다시 쓰기"),
    "grammar": ("문법 형태(be동사·비교급·of 누락 등)", "be동사와 일반동사를 겹쳐 쓰지 않기(I am agree ✗), 비교급·최상급에 more/most 겹쳐 쓰지 않기, thousands of처럼 필요한 of 챙기기.",
                "자주 틀린 문장 3개를 골라 올바른 형태로 5번씩 소리 내어 읽기"),
    "spelling": ("철자", "자주 틀리는 단어를 모아 두고 제출 전에 확인하세요.", "틀린 철자 단어 5개를 세 번씩 써 보기"),
    "punctuation": ("구두점·띄어쓰기", "쉼표·마침표 뒤 한 칸, 문장 끝 마침표.", "제출 전 마지막 10초 점검 습관"),
    "capitalization": ("대문자", "문장 첫 글자와 I는 대문자.", "제출 전 마지막 10초 점검 습관"),
    "repetition": ("단어 반복", "같은 단어가 연속으로 반복되지 않았는지 확인하세요.", "소리 내어 읽고 제출하기"),
    "awkward": ("어색한 중복 표현", "in my opinion과 I think처럼 같은 뜻을 겹쳐 쓰지 마세요.", "의견 표현 문형 5개를 번갈아 쓰기"),
}
SCORE_KO = {"grammar": "문법", "vocabulary": "어휘", "naturalness": "자연스러움", "content": "내용 구성"}


def build_report(answers, days, settings):
    if not answers:
        return {"empty": True}
    by_day = defaultdict(list)
    for a in answers:
        by_day[a["date"]].append(a)

    # latest attempt per question counts for scores
    latest = {}
    for a in answers:
        latest[(a["date"], a["pi"], a["qi"])] = a
    L = list(latest.values())

    daily = []
    for date in sorted(set(by_day) | set(d["date"] for d in days)):
        day = next((d for d in days if d["date"] == date), None)
        passages = len(day["passages"]) if day else 0
        questions = sum(len(p["questions"]) for p in day["passages"]) if day else 0
        lat = [a for a in L if a["date"] == date]
        daily.append({"date": date, "passages_total": passages, "questions_total": questions,
                      "passages_read": len({a["pi"] for a in lat}), "answered": len(lat),
                      "attempts": len(by_day.get(date, [])),
                      "avg": round(sum(a["overall"] for a in lat) / len(lat), 2) if lat else None})

    sub = {k: [a["feedback"]["scores"][k] for a in L] for k in SCORE_KO}
    sub_avg = {k: round(sum(v) / len(v), 2) for k, v in sub.items() if v}
    overall_avg = round(sum(a["overall"] for a in L) / len(L), 2)

    types, examples = Counter(), defaultdict(list)
    for a in L:
        for c in a["feedback"]["corrections"]:
            if c["category"] == "style" or not c.get("original"):
                continue
            types[c["type"]] += 1
            if len(examples[c["type"]]) < 3 and c.get("corrected"):
                examples[c["type"]].append(f"{c['original']} → {c['corrected']}")

    # trend: first half vs second half (by time)
    ordered = sorted(L, key=lambda a: a["id"])
    half = len(ordered) // 2
    trend = None
    if half >= 2:
        first = sum(a["overall"] for a in ordered[:half]) / half
        second = sum(a["overall"] for a in ordered[half:]) / (len(ordered) - half)
        trend = round(second - first, 2)

    today = dt.date.today()
    last14 = {(today - dt.timedelta(days=i)).isoformat() for i in range(14)}
    active14 = len([d for d in daily if d["date"] in last14 and d["answered"]])
    streak = 0
    for i in range(0, 60):
        if any(d["date"] == (today - dt.timedelta(days=i)).isoformat() and d["answered"] for d in daily):
            streak += 1
        elif i > 0:
            break
    per_day = round(len(L) / max(1, len([d for d in daily if d["answered"]])), 1)
    target_per_day = settings["passages"] * settings["questions"]

    # level from average score
    if overall_avg >= 8.5:
        level = "C1 수준(추정): 오류가 적고 어휘가 다양합니다. 이제는 표현의 정교함과 논리 전개를 다듬을 단계예요."
    elif overall_avg >= 7:
        level = "B2 수준(추정): 의사 전달은 충분히 되지만 반복되는 문법 패턴 몇 가지가 점수를 깎고 있어요."
    elif overall_avg >= 5.5:
        level = "B1 수준(추정): 기본 문장은 안정적이에요. 수 일치·전치사 같은 기초 규칙을 굳히면 빠르게 올라갑니다."
    else:
        level = "A2~B1 수준(추정): 짧고 정확한 문장부터 차근차근 쌓아 가는 게 가장 효과적인 단계예요."

    strengths = []
    for k, v in sorted(sub_avg.items(), key=lambda kv: -kv[1])[:2]:
        strengths.append(f"{SCORE_KO[k]} 평균 {v:.1f}점")
    adv = [a["feedback"]["stats"]["advanced_ratio"] for a in L]
    if adv and sum(adv) / len(adv) >= 0.15:
        strengths.append("수준 높은 단어 비율이 높습니다(평균 {:.0%}).".format(sum(adv) / len(adv)))

    MECH = ("capitalization", "punctuation", "repetition")
    ranked = [tc for tc in types.most_common() if tc[0] not in MECH] + [tc for tc in types.most_common() if tc[0] in MECH]
    issues = []
    for t, c in ranked[:4]:
        name, fix, _ = ADVICE.get(t, (t, "", ""))
        issues.append({"type": t, "pattern_ko": f"{name} — {c}회", "examples": examples[t], "fix_ko": fix})

    direction = []
    if active14 >= 10:
        direction.append(f"최근 14일 중 {active14}일 공부했어요. 꾸준함은 충분합니다.")
    elif active14 >= 5:
        direction.append(f"최근 14일 중 {active14}일 공부했어요. 주 5일 이상으로 늘리면 실력이 더 빨리 붙습니다.")
    else:
        direction.append(f"최근 14일 중 {active14}일만 공부했어요. 분량을 줄이더라도 매일 하는 것이 가장 중요합니다.")
    direction.append(f"하루 평균 {per_day}문항에 답했어요(설정 기준 {target_per_day}문항).")
    if trend is not None:
        if trend > 0.3:
            direction.append(f"전반부보다 후반부 평균이 {trend:+.1f}점 올랐어요. 지금 방식이 효과가 있습니다.")
        elif trend < -0.3:
            direction.append(f"후반부 평균이 {trend:+.1f}점 내려갔어요. 지문 난이도나 답변 길이가 늘었는지 확인하고, 오답 유형 복습을 먼저 해 보세요.")
        else:
            direction.append("점수가 비슷한 수준을 유지하고 있어요. 새로운 문형과 단어를 의식적으로 섞어 써야 다음 단계로 넘어갑니다.")
    if types:
        top = ranked[0][0]
        direction.append(f"가장 먼저 잡을 것은 '{ADVICE.get(top, (top,))[0]}'입니다. 이것만 줄여도 문법 점수가 눈에 띄게 오릅니다.")
    weakest = min(sub_avg, key=sub_avg.get)
    direction.append(f"점수가 가장 낮은 영역은 {SCORE_KO[weakest]}입니다.")

    plan = []
    for t, _ in ranked[:3]:
        plan.append(ADVICE.get(t, (t, "", f"{t} 복습"))[2])
    if sub_avg.get("vocabulary", 10) < 7:
        plan.append("단어장에서 매일 5개를 골라 그날 답변에 일부러 넣어 쓰기")
    if sub_avg.get("content", 10) < 7:
        plan.append("답변을 '의견 → 이유 → 예시 → 마무리' 4문장 틀로 쓰기")
    plan.append("지난 첨삭에서 '고쳐서 다시 쓰기'를 한 문항 이상 해 보기")
    plan.append("주말에 이번 주 교정 내역을 다시 읽고 같은 실수 표시하기")

    rec = []
    if overall_avg >= 8 and per_day >= target_per_day * 0.8:
        rec.append("평균 8점 이상이고 분량도 잘 채우고 있어요. 지문 길이를 '길게'로 올리거나 지문당 질문을 1개 늘려 보세요.")
    elif per_day < target_per_day * 0.5:
        rec.append(f"설정된 분량({target_per_day}문항)의 절반도 못 채우는 날이 많아요. 지문 수를 줄여 매일 끝까지 하는 경험을 쌓으세요.")
    elif overall_avg < 6:
        rec.append("지문 길이를 '짧게'로 줄이고 질문 수를 1~2개로 해서 정확도부터 올려 보세요.")
    else:
        rec.append("지금 설정이 적당합니다.")

    return {"empty": False, "level_ko": level, "overall_avg": overall_avg, "sub_avg": sub_avg, "daily": daily,
            "error_types": types.most_common(), "strengths_ko": strengths, "recurring_issues": issues,
            "direction_ko": " ".join(direction), "plan": plan, "settings_ko": " ".join(rec),
            "streak": streak, "active14": active14, "answered_total": len(L), "attempts_total": len(answers),
            "trend": trend}
