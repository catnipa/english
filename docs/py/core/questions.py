"""Opinion questions from fixed templates (no AI). The day's date + story id seeds the choice,
so the same day always gives the same questions, and different stories get different kinds."""
import random

T = {
    "opinion": [
        ("What is your opinion on this story: “{title}”? Explain your reasons with at least two points.",
         "In my view, … / I'm inclined to think … / The main reason is that …"),
        ("Do you think the people or organizations involved made the right decision? Why or why not?",
         "I'd argue that … / It was a reasonable move because … / In hindsight, …"),
        ("Who do you think is most responsible for this situation, and what should they do now?",
         "The responsibility lies with … / They should have … / What needs to happen now is …"),
    ],
    "emotion": [
        ("How did you feel when you read this story? Describe your reaction and explain why you felt that way.",
         "I was taken aback by … / It's frustrating that … / I felt relieved when …"),
        ("If you were directly affected by this news, how would you feel and what would you do?",
         "If I were in their shoes, I would … / I'd probably feel … / The first thing I'd do is …"),
    ],
    "business": [
        ("How could this news affect businesses, investors or consumers? Give a concrete example.",
         "This could weigh on … / Investors are likely to … / For consumers, it means …"),
        ("If you were a manager at a company affected by this story, what would you do next week?",
         "My priority would be to … / I'd set up a meeting to … / We would need to reassess …"),
    ],
    "prediction": [
        ("What do you think will happen next? Make a prediction and give two reasons.",
         "I expect that … / It remains to be seen whether … / In the long run, …"),
        ("Is this a short-term issue or a sign of a bigger, long-term trend? Explain.",
         "This is just the tip of the iceberg … / It's likely a one-off … / The bigger picture is …"),
    ],
    "korea": [
        ("Could something similar happen in Korea? How would Korean society or companies react?",
         "In Korea, … would likely … / Unlike the US, Korea … / Korean companies tend to …"),
        ("What can Korea learn from this story? Suggest one lesson.",
         "One lesson for Korea is … / We should take this as a wake-up call to …"),
    ],
    "personal": [
        ("Has anything in your own life or work been similar to this story? Describe it briefly.",
         "This reminds me of a time when … / I can relate to this because … / At my workplace, …"),
        ("Explain this story to a friend in your own words, then add your one-sentence opinion.",
         "In a nutshell, … / What happened was … / Personally, I think …"),
    ],
}

ORDER_BY_CAT = {
    "Markets": ["business", "prediction", "opinion", "korea", "emotion", "personal"],
    "Business": ["business", "opinion", "korea", "prediction", "personal", "emotion"],
    "Tech": ["opinion", "business", "prediction", "korea", "personal", "emotion"],
    "Politics": ["opinion", "prediction", "korea", "emotion", "personal", "business"],
    "World": ["emotion", "opinion", "prediction", "korea", "personal", "business"],
    "Society": ["emotion", "personal", "opinion", "korea", "prediction", "business"],
}
TYPE_KO = {"opinion": "의견", "emotion": "감정", "business": "비즈니스", "prediction": "전망", "korea": "한국과 비교",
           "personal": "내 경험"}

# phrase bank used by the corrector to suggest expressions that fit the question type
PHRASE_BANK = {
    "opinion": [("In my view, …", "내 생각에는"), ("I'm inclined to think that …", "~라고 생각하는 쪽이다"),
                ("I'd argue that …", "~라고 주장하고 싶다"), ("The way I see it, …", "내가 보기에는"),
                ("That said, …", "그렇긴 하지만"), ("On balance, …", "모든 걸 고려하면")],
    "emotion": [("I was taken aback by …", "~에 깜짝 놀랐다"), ("It's heartbreaking to see …", "~을 보니 가슴 아프다"),
                ("I felt a sense of relief when …", "~할 때 안도감을 느꼈다"), ("It's frustrating that …", "~해서 답답하다"),
                ("I can't help feeling that …", "~라는 느낌을 지울 수 없다"), ("It really struck a chord with me.", "크게 공감됐다")],
    "business": [("This could weigh on …", "~에 부담이 될 수 있다"), ("It's likely to drive up costs.", "비용을 끌어올릴 것 같다"),
                 ("Investors may take a wait-and-see approach.", "투자자들은 관망할 수 있다"),
                 ("From a business standpoint, …", "비즈니스 관점에서"), ("The bottom line is …", "요점은"),
                 ("It could be a game changer for …", "~에게 판도를 바꿀 수 있다")],
    "prediction": [("It remains to be seen whether …", "~일지는 지켜봐야 한다"), ("I expect … to …", "~가 ~할 것으로 예상한다"),
                   ("In the long run, …", "장기적으로"), ("Chances are that …", "아마 ~일 것이다"),
                   ("This is just the tip of the iceberg.", "이건 빙산의 일각이다"), ("Down the road, …", "앞으로")],
    "korea": [("Unlike the US, Korea …", "미국과 달리 한국은"), ("In the Korean context, …", "한국 상황에서는"),
              ("This should be a wake-up call for …", "~에게 경종이 되어야 한다"), ("Korea could learn from …", "한국은 ~에서 배울 수 있다")],
    "personal": [("This reminds me of a time when …", "~했던 때가 떠오른다"), ("I can relate to this because …", "~라서 공감한다"),
                 ("In a nutshell, …", "한마디로"), ("Speaking from experience, …", "경험상")],
}


def make_questions(story, count, seed):
    rng = random.Random(seed)
    kinds = ORDER_BY_CAT.get(story["category"], list(T))[:]
    head, rest = kinds[:1], kinds[1:]
    rng.shuffle(rest)
    out = []
    for kind in (head + rest)[:count]:
        q, hint = rng.choice(T[kind])
        out.append({"q": q.format(title=story["title"]), "hint_ko": "써 볼 표현: " + hint, "type": kind,
                    "type_ko": TYPE_KO[kind]})
    return out
