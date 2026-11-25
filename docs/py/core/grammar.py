"""Rule-based English checker for Korean learners. No AI, no statistics models: every finding comes
from an explicit rule below, with a Korean explanation written by hand.

Optional extras (both rule-based, both off by default):
- a word list for spelling (e.g. /usr/share/dict/words on macOS/Linux)
- LanguageTool (open-source rule-based grammar checker) via its HTTP API
"""
import json
import os
import re
import urllib.parse
import urllib.request

from .textutil import sentences, words

# ---------------------------------------------------------------------------------------------
# helpers
NUMWORDS = r"(?:\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|several|many|a few)"
SING_NOUNS_FOR_ONE_OF = {"reason": "reasons", "problem": "problems", "issue": "issues", "way": "ways",
                         "thing": "things", "factor": "factors", "company": "companies", "country": "countries",
                         "person": "people", "example": "examples", "cause": "causes", "solution": "solutions",
                         "challenge": "challenges", "story": "stories", "benefit": "benefits", "risk": "risks",
                         "city": "cities", "leader": "leaders", "event": "events", "case": "cases",
                         "friend": "friends", "member": "members", "idea": "ideas", "point": "points"}
EVERY_PLURAL = {"days": "day", "times": "time", "weeks": "week", "years": "year", "months": "month",
                "students": "student", "people": "person", "persons": "person", "companies": "company",
                "countries": "country", "mornings": "morning", "nights": "night"}
UNCOUNTABLE = {"informations": "information", "advices": "advice", "furnitures": "furniture",
               "equipments": "equipment", "evidences": "evidence", "knowledges": "knowledge",
               "homeworks": "homework", "luggages": "luggage", "baggages": "baggage", "feedbacks": "feedback",
               "softwares": "software", "machineries": "machinery", "jewelries": "jewelry", "trafics": "traffic",
               "traffics": "traffic", "progresses": "progress", "researchs": "research"}
IRREG_PAST = {"rised": "rose", "costed": "cost", "buyed": "bought", "teached": "taught", "thinked": "thought",
              "goed": "went", "catched": "caught", "bringed": "brought", "runned": "ran", "writed": "wrote",
              "choosed": "chose", "losed": "lost", "payed": "paid", "sayed": "said", "leaded": "led",
              "spended": "spent", "sended": "sent", "builded": "built", "feeled": "felt", "falled": "fell",
              "growed": "grew", "knowed": "knew", "meaned": "meant", "sleeped": "slept", "speaked": "spoke",
              "standed": "stood", "stealed": "stole", "swimmed": "swam", "taked": "took", "telled": "told",
              "understanded": "understood", "weared": "wore", "winned": "won", "hitted": "hit", "putted": "put",
              "cutted": "cut", "shutted": "shut", "setted": "set", "beginned": "began", "breaked": "broke",
              "drived": "drove", "eated": "ate", "forgeted": "forgot", "forgetted": "forgot", "getted": "got",
              "gived": "gave", "hided": "hid", "holded": "held", "keeped": "kept", "maked": "made",
              "meeted": "met", "selled": "sold", "shooted": "shot", "singed": "sang", "sitted": "sat",
              "throwed": "threw", "leaved": "left", "fighted": "fought", "seeked": "sought", "flied": "flew",
              "drinked": "drank", "finded": "found", "comed": "came", "becomed": "became", "striked": "struck"}
MISSPELL = {"recieve": "receive", "beleive": "believe", "goverment": "government", "enviroment": "environment",
            "buisness": "business", "bussiness": "business", "definately": "definitely", "seperate": "separate",
            "untill": "until", "wich": "which", "becuase": "because", "beacuse": "because", "becasue": "because",
            "tommorow": "tomorrow", "tomorow": "tomorrow", "occured": "occurred", "occurence": "occurrence",
            "accomodate": "accommodate", "acommodate": "accommodate", "adress": "address", "begining": "beginning",
            "beleif": "belief", "calender": "calendar", "comming": "coming", "commitee": "committee",
            "concious": "conscious", "dissapoint": "disappoint", "dissapointed": "disappointed",
            "embarass": "embarrass", "embarassed": "embarrassed", "existance": "existence", "familar": "familiar",
            "finaly": "finally", "foriegn": "foreign", "freind": "friend", "garantee": "guarantee",
            "grammer": "grammar", "happend": "happened", "immediatly": "immediately", "independant": "independent",
            "interupt": "interrupt", "knowlege": "knowledge", "libary": "library", "maintainance": "maintenance",
            "neccessary": "necessary", "necesary": "necessary", "noticable": "noticeable", "occassion": "occasion",
            "oppurtunity": "opportunity", "oportunity": "opportunity", "persue": "pursue", "posession": "possession",
            "prefered": "preferred", "propably": "probably", "probaly": "probably", "realy": "really",
            "recomend": "recommend", "reccomend": "recommend", "relevent": "relevant", "responsability": "responsibility",
            "succesful": "successful", "successfull": "successful", "suprise": "surprise", "suprised": "surprised",
            "thier": "their", "truely": "truly", "wierd": "weird", "writting": "writing", "alot": "a lot",
            "economicly": "economically", "goverments": "governments", "comapny": "company", "compnay": "company",
            "investement": "investment", "managment": "management", "importent": "important", "diffrent": "different",
            "intrest": "interest", "intresting": "interesting", "beautifull": "beautiful", "wonderfull": "wonderful",
            "studing": "studying", "stoped": "stopped", "planed": "planned", "droped": "dropped"}
VERY_UPGRADE = {"good": "excellent", "bad": "terrible", "important": "crucial", "big": "huge", "small": "tiny",
                "happy": "delighted", "sad": "heartbroken", "surprised": "astonished", "angry": "furious",
                "tired": "exhausted", "interesting": "fascinating", "worried": "deeply concerned",
                "scared": "terrified", "difficult": "challenging", "hard": "tough", "serious": "grave",
                "bad news": "devastating news", "dangerous": "perilous", "expensive": "pricey", "cheap": "inexpensive",
                "fast": "rapid", "old": "ancient", "clear": "obvious", "smart": "brilliant", "strong": "powerful",
                "disappointed": "dismayed", "upset": "distraught", "busy": "swamped", "shocked": "stunned",
                "bored": "fed up", "excited": "thrilled", "different": "strikingly different", "many": "numerous"}
AGREE_VERBS = {"look", "seem", "need", "want", "make", "go", "become", "cause", "mean", "depend", "show", "remain", "affect", "feel", "work", "happen", "matter", "cost", "grow", "keep", "help"}
COLLECTIVE = {"people", "police", "staff", "team", "government", "family", "media", "data", "public", "children", "crew", "majority"}
PLURAL_CAPS = {"they", "we", "you", "i", "people", "many", "some", "both", "others", "most", "all", "these", "those", "few", "several", "police", "children", "americans", "koreans", "investors", "analysts", "democrats", "republicans", "we'll"}
STOP_SUBJ = {"you", "they", "we", "who", "which", "what", "she", "him", "them", "her", "his", "its", "our", "your", "their", "most", "only", "same", "other", "first", "last", "best", "worst", "next", "main", "few", "one", "many", "more", "two", "they", "both", "all"}
BASE_VERBS = ("go want need like think make take say know get seem look feel work live believe try mean plan "
              "become cause show help depend affect agree love hate hope expect play run come give tell use "
              "happen matter remain include require mean prefer understand care seem want need know trust lose win pay cost hurt keep stay change support oppose face ignore worry decide").split()
MODALS = {"can", "could", "will", "would", "should", "shall", "may", "might", "must", "did", "does", "do",
          "to", "let", "make", "help", "not", "n't", "won't", "didn't", "doesn't", "don't", "cannot", "can't",
          "never", "always", "also", "often", "usually", "really", "just", "only", "still", "even"}
AN_EXCEPT_CONSONANT_SOUND = ("uni", "use", "usu", "uti", "eu", "one", "once", "ubiq", "ukr", "uran", "ure")
AN_EXCEPT_VOWEL_SOUND = ("hour", "honest", "honor", "honour", "heir", "herb")


def third_person(v):
    if v == "have":
        return "has"
    if v in ("go", "do"):
        return v + "es"
    if re.search(r"[^aeiou]y$", v):
        return v[:-1] + "ies"
    if re.search(r"(s|sh|ch|x|z)$", v):
        return v + "es"
    return v + "s"


def keep_case(orig, new):
    if orig[:1].isupper() and new:
        return new[0].upper() + new[1:]
    return new


# ---------------------------------------------------------------------------------------------
# regex rules: (pattern, replacement or function(match)->str|None, type, explanation_ko, autofix)
R = []


def rule(pattern, repl, typ, ko, autofix=True, flags=re.I):
    R.append((re.compile(pattern, flags), repl, typ, ko, autofix))


# collocations / prepositions Korean speakers often add or drop
rule(r"\b(discuss(?:es|ed|ing)?) about\b", r"\1", "preposition", "discuss는 타동사라 about 없이 바로 목적어를 씁니다. (discuss the issue)")
rule(r"\b(emphasi[sz](?:e|es|ed|ing)) on\b", r"\1", "preposition", "emphasize는 타동사입니다. emphasize on이 아니라 emphasize the point. (명사 emphasis는 on과 함께: put emphasis on)")
rule(r"\b(mention(?:s|ed|ing)?) about\b", r"\1", "preposition", "mention은 타동사라 about이 필요 없습니다. (mention the problem)")
rule(r"\b(contact(?:s|ed|ing)?) (?:to|with) (?=\w)", r"\1 ", "preposition", "contact는 타동사입니다. contact to/with 대신 contact someone.")
rule(r"\b(reach(?:es|ed|ing)?) to (?=(?:a|an|the|an?|\d|\$|record|agreement|deal|consensus|conclusion|decision)\b)", r"\1 ", "preposition", "'~에 도달하다'의 reach는 타동사입니다. reach an agreement / reach $10 billion.")
rule(r"\b(approach(?:es|ed))\s+to\b", r"\1", "preposition", "동사 approach는 to 없이 씁니다. (They approached the problem.) 명사 an approach to는 맞습니다.")
rule(r"\b(marr(?:y|ies|ied|ying)) with\b", r"\1", "preposition", "marry는 with 없이 씁니다. (She married him / got married to him)")
rule(r"\b(attend(?:s|ed|ing)?) to (?=(?:the |a |an )?(?:meeting|class|conference|event|lecture|ceremony|wedding|school|seminar|session)s?\b)", r"\1 ", "preposition", "'참석하다'의 attend는 타동사입니다. attend to는 '처리하다/돌보다'라는 다른 뜻이에요.")
rule(r"\b(enter(?:s|ed|ing)?) into (?=(?:the |a |an |my |our )?(?:room|building|office|house|school|country|store|shop|company|market)\b)", r"\1 ", "preposition", "장소에 '들어가다'는 enter the room. enter into는 '계약·협상을 맺다'에 씁니다.")
rule(r"\b(join(?:s|ed|ing)?) to (?=(?:the |a |an |our |my )?\w)", r"\1 ", "preposition", "join은 타동사입니다. join the team.")
rule(r"\bexplain(s|ed|ing)? me\b", r"explain\1 to me", "structure", "explain 다음에 사람이 바로 올 수 없습니다. explain it to me / explain to me how …")
rule(r"\bsay(s)? me\b", r"tell\1 me", "word_choice", "say는 사람 목적어를 바로 받지 않습니다. tell me / say to me.")
rule(r"\bsaid me\b", "told me", "word_choice", "say는 사람 목적어를 바로 받지 않습니다. told me / said to me.")
rule(r"\b(suggest(?:s|ed)?) (me|him|her|us|them) to (\w+)", lambda m: f"{m.group(1)} that {({'me':'I','him':'he','her':'she','us':'we','them':'they'})[m.group(2).lower()]} {m.group(3)}", "structure", "suggest는 'suggest + 사람 + to부정사' 구조를 쓰지 않습니다. suggest that I (should) go / suggest going.")
rule(r"\b(let|make|made|lets|makes) (me|him|her|us|them|people|it) to (\w+)", r"\1 \2 \3", "structure", "사역동사 let/make 다음에는 to 없이 동사원형을 씁니다. (let me know, made me feel)")
rule(r"\bdespite of\b", "despite", "preposition", "despite 뒤에는 of를 쓰지 않습니다. (in spite of는 of가 필요)")
rule(r"\baccording to me\b", "in my opinion", "word_choice", "according to는 다른 사람·자료를 인용할 때 씁니다. 내 의견은 in my opinion / in my view.")
rule(r"\bin my (opinion|view),? i think\b", r"in my \1,", "awkward", "in my opinion과 I think는 같은 뜻이라 중복입니다. 하나만 쓰세요.")
rule(r"\b(i|we|they|you)(?:\s+am|\s+are|['’]m|['’]re)\s+(agree|disagree)\b", r"\1 \2", "grammar", "agree는 동사입니다. I am agree가 아니라 I agree.")
rule(r"\b(i|we|they|you)(\s+am|\s+are|['’]m|['’]re)\s+(very |really |so )?interesting in\b", r"\1\2 \3interested in", "word_choice", "내가 관심을 느끼면 interested, 대상이 흥미를 주면 interesting. I'm interested in …")
rule(r"\b(?:i|we)(?:\s+am|\s+are|['’]m|['’]re)\s+(?:so |very |really )?boring\b", None, "word_choice", "I'm boring은 '나는 지루한 사람이다'라는 뜻입니다. 지루함을 느낀다면 I'm bored.", False)
rule(r"\bmore (better|worse|easier|bigger|cheaper|faster|smarter|stronger|larger|higher|lower|harder|happier|longer|younger|older|richer|greater)\b", r"\1", "grammar", "비교급(-er, better)에는 more를 또 붙이지 않습니다.")
rule(r"\b(?:the )?most (best|worst|biggest|largest|highest|easiest|greatest|smallest|richest)\b", r"the \1", "grammar", "최상급(-est, best)에는 most를 또 붙이지 않습니다.")
rule(r"\bsince (" + NUMWORDS + r") (years|months|weeks|days|hours|decades)\b", r"for \1 \2", "preposition", "기간(얼마 동안)은 for, 시작 시점(언제부터)은 since. for three years / since 2020.")
rule(r"\bduring (" + NUMWORDS + r") (years|months|weeks|days|hours|decades)\b", r"for \1 \2", "preposition", "숫자로 된 기간 앞에는 during 대신 for를 씁니다. (during은 during the meeting처럼 특정 기간 명사 앞)")
rule(r"\blook(s|ed|ing)? forward to (see|meet|hear|work|talk|visit|get|have|go|discuss|receive)\b", lambda m: f"look{m.group(1) or ''} forward to {m.group(2)[:-1] if m.group(2).endswith('e') and m.group(2) not in ('see',) else m.group(2)}ing", "grammar", "look forward to의 to는 전치사라 뒤에 -ing가 옵니다. (look forward to seeing you)")
rule(r"\bhow do you think\b", "what do you think", "word_choice", "'어떻게 생각해?'는 What do you think? (how는 방법을 물을 때)")
rule(r"\b(it|this|that) (?:is|'s) depend(?:s|ed)? (?:on|of)\b", r"\1 depends on", "grammar", "depend는 동사입니다. it is depend → it depends on.")
rule(r"\bdepend(s|ed|ing)? of\b", r"depend\1 on", "preposition", "depend 뒤에는 on을 씁니다.")
rule(r"\b(?:do|did|does|doing) (?:a |many |some |lots of |a lot of )?(mistakes?)\b", lambda m: m.group(0).replace(m.group(0).split()[0], {"do": "make", "did": "made", "does": "makes", "doing": "making"}[m.group(0).split()[0].lower()]), "collocation", "'실수하다'는 make a mistake입니다. (do가 아니라 make)")
rule(r"\b(?:make|made|makes|making) (?:my |the |our |his |her )?homework\b", lambda m: m.group(0).replace(m.group(0).split()[0], {"make": "do", "made": "did", "makes": "does", "making": "doing"}[m.group(0).split()[0].lower()]), "collocation", "'숙제하다'는 do homework입니다.")
rule(r"\b(strong|big) (rain|rainfall)\b", r"heavy \2", "collocation", "'폭우'는 heavy rain이라고 합니다.")
rule(r"\b(price|prices|cost|costs|salary|salaries|fee|fees) (is|are|was|were) (?:very |so |too )?expensive\b", r"\1 \2 high", "collocation", "price 자체가 비싼 게 아니라 높은 것입니다. The price is high / The product is expensive.")
rule(r"\b(price|prices|cost|costs|salary|salaries|fee|fees) (is|are|was|were) (?:very |so |too )?cheap\b", r"\1 \2 low", "collocation", "price에는 cheap 대신 low를 씁니다. The price is low.")
rule(r"\bcheap (price|prices|cost|costs)\b", r"low \1", "collocation", "price와 함께는 low price / affordable price.")
rule(r"\bexpensive (price|prices|cost|costs)\b", r"high \1", "collocation", "price와 함께는 high price.")
rule(r"\b(go|went|goes|going|come|came|comes|coming|get|got|return|returned) to (home|abroad|there|here|downtown|overseas)\b", r"\1 \2", "preposition", "home, abroad, there, here, downtown은 부사라 to 없이 씁니다. (go home, go abroad)")
rule(r"\balmost (people|everyone|all of|students|companies|koreans|americans)\b", lambda m: "most " + m.group(1) if m.group(1).lower() != "all of" else "almost all of", "word_choice", "almost는 부사라 명사를 바로 꾸미지 못합니다. most people / almost all people.")
rule(r"\balmost of\b", "most of", "word_choice", "'대부분의'는 most of. almost는 almost all of처럼 씁니다.")
rule(r"\bevery (" + "|".join(EVERY_PLURAL) + r")\b", lambda m: "every " + EVERY_PLURAL[m.group(1).lower()], "agreement", "every 뒤에는 단수 명사가 옵니다. (every day, every company)")
rule(r"\bone of the (?:most \w+ |biggest |main |key |major |best |worst )?(" + "|".join(SING_NOUNS_FOR_ONE_OF) + r")\b", lambda m: m.group(0)[: -len(m.group(1))] + SING_NOUNS_FOR_ONE_OF[m.group(1).lower()], "agreement", "one of the 뒤에는 복수 명사가 옵니다. (one of the reasons)")
rule(r"\b(" + "|".join(UNCOUNTABLE) + r")\b", lambda m: keep_case(m.group(1), UNCOUNTABLE[m.group(1).lower()]), "agreement", "셀 수 없는 명사라 -s를 붙이지 않습니다. (information, advice, equipment …)")
rule(r"\bpeople (is|was|has|does|doesn't)\b", lambda m: "people " + {"is": "are", "was": "were", "has": "have", "does": "do", "doesn't": "don't"}[m.group(1).lower()], "agreement", "people은 복수라 are/were/have를 씁니다.")
rule(r"\b(everyone|everybody|someone|somebody|nobody|no one|anyone|anybody|each person) (are|were|have|don't|do)\b", lambda m: m.group(1) + " " + {"are": "is", "were": "was", "have": "has", "don't": "doesn't", "do": "does"}[m.group(2).lower()], "agreement", "everyone, someone, nobody 등은 단수 취급합니다. (Everyone is …)")
rule(r"\b(he|she|it|this|that) (don't|dont|have|are|were|do)\b(?! to\b)", lambda m: m.group(1) + " " + {"don't": "doesn't", "dont": "doesn't", "have": "has", "are": "is", "were": "was", "do": "does"}[m.group(2).lower()], "agreement", "3인칭 단수 주어(he, she, it)에는 doesn't / has / is / was를 씁니다.")
rule(r"\b(you|we|they) was\b", r"\1 were", "agreement", "you/we/they 뒤에는 were를 씁니다.")
rule(r"\b(we|they) (is|has|does|doesn't)\b", lambda m: m.group(1) + " " + {"is": "are", "has": "have", "does": "do", "doesn't": "don't"}[m.group(2).lower()], "agreement", "복수 주어 we/they에는 are/have/do를 씁니다.")
rule(r"\bthere (is|was) ((?:many|a lot of|lots of|several|some|few|a few|two|three|four|five|\d+) \w+s)\b", lambda m: "there " + ("are" if m.group(1).lower() == "is" else "were") + " " + m.group(2), "agreement", "뒤에 복수 명사가 오면 there are / there were.")
rule(r"\b(" + "|".join(IRREG_PAST) + r")\b", lambda m: keep_case(m.group(1), IRREG_PAST[m.group(1).lower()]), "tense", "불규칙 동사의 과거형입니다. (rise-rose, cost-cost, buy-bought …)")
rule(r"\bif (i|you|we|they|he|she|it) will (\w+)", lambda m: m.group(0)[:2] + " " + m.group(1) + " " + (third_person(m.group(2).lower()) if m.group(1).lower() in ("he", "she", "it") and m.group(2).lower() not in ("be", "not") else ("is" if m.group(2).lower() == "be" and m.group(1).lower() in ("he","she","it") else m.group(2))), "tense", "조건을 나타내는 if절에서는 미래라도 현재형을 씁니다. (If it rains tomorrow, …)")
rule(r"\b(too much) (people|companies|cars|problems|things|students|jobs|countries|times|stores|flights|questions)\b", r"too many \2", "agreement", "셀 수 있는 복수 명사에는 much 대신 many. (too many people)")
rule(r"\b(a lot|alot) (people|companies|things|problems)\b", r"a lot of \2", "grammar", "a lot 뒤에 명사가 오면 a lot of.")
rule(r"\b(i|we|they|you) (?:am|are|'m|'re) (?:very |so |really )?concern(?:ed)? (?:about|for|with)?\b", lambda m: re.sub(r"concern(?:ed)?", "concerned", m.group(0)), "grammar", "'걱정한다'는 be concerned about (concern은 '걱정시키다'). I'm concerned about …")
rule(r"\b(i|we|they|you) concern about\b", r"\1 am concerned about", "grammar", "'~이 걱정된다'는 be concerned about입니다. (I'm concerned about …)")
rule(r"\b(?:i|we) (?:was|were|am|are|'m|'re) (?:very |so |really )?(?:surprise|shock|disappoint|excite|worry|embarrass|confuse|interest|satisfy)\b", lambda m: m.group(0) + ("d" if m.group(0).endswith("e") else "ed") if not m.group(0).endswith("y") else m.group(0)[:-1] + "ied", "word_choice", "감정을 느끼는 사람은 -ed 형태입니다. (I was surprised / worried)")
rule(r"\b(could|should|would|must|might|may|can|will) (went|did|had|was|made|took|came|got|saw|gave|said|knew|thought|told)\b", lambda m: m.group(1) + " " + {"went": "go", "did": "do", "had": "have", "was": "be", "made": "make", "took": "take", "came": "come", "got": "get", "saw": "see", "gave": "give", "said": "say", "knew": "know", "thought": "think", "told": "tell"}[m.group(2).lower()], "grammar", "조동사 뒤에는 동사원형이 옵니다. (과거라면 should have gone처럼 have + p.p.)")
rule(r"\b(to) (went|did|was|made|took|came|got|saw|gave|said|knew|thought|told|bought)\b", lambda m: "to " + {"went": "go", "did": "do", "was": "be", "made": "make", "took": "take", "came": "come", "got": "get", "saw": "see", "gave": "give", "said": "say", "knew": "know", "thought": "think", "told": "tell", "bought": "buy"}[m.group(2).lower()], "grammar", "to부정사 뒤에는 동사원형이 옵니다.")
rule(r"\b(can|don|doesn|didn|isn|aren|wasn|weren|won|wouldn|shouldn|couldn|haven|hasn|hadn)t\b", lambda m: m.group(1) + ("'t" if m.group(1).lower() != "can" else "'t"), "punctuation", "축약형에는 아포스트로피(')가 필요합니다. (can't, don't, doesn't)")
rule(r"\b(?:the|this|that|my|our|his|her|their|its|your) (?!(?:" + "|".join(sorted({"government","team","family","staff","police","people","children","media","data","public","crew","audience","committee","board","news","majority","series","species","press","company's"})) + r")\b)([a-z]{3,}?[^s\W]) (have|haven't|don't|dont|were|are)\b(?! to\b)", lambda m: None if m.group(1) in STOP_SUBJ else m.group(0)[: -len(m.group(2))] + {"have": "has", "haven't": "hasn't", "don't": "doesn't", "dont": "doesn't", "were": "was", "are": "is"}[m.group(2).lower()], "agreement", "주어가 단수 명사(the system, my company)이면 has / doesn't / is / was를 씁니다.")
rule(r"\b(thousands|hundreds|millions|dozens|tens) (?!of\b)([a-z]+s)\b", r"\1 of \2", "grammar", "'수천 개의 ~'는 thousands of flights처럼 of가 필요합니다.")
rule(r"\b((?:many|several|these|those|both|\d[\d,]*|two|three|four|five|ten|thousands of|hundreds of|millions of|dozens of|a lot of|lots of) (?:[a-z]+ )?[a-z]+s) (was|is|has|doesn't)\b", lambda m: m.group(1) + " " + {"was": "were", "is": "are", "has": "have", "doesn't": "don't"}[m.group(2).lower()], "agreement", "주어가 복수(many flights, these companies)이면 were / are / have를 씁니다.")
rule(r"\b(?!(?:series|species|news|movies|politics|economics|physics|athletics)\b)([a-z]{2,}(?:ers|ors|ies|ants|ents|ists|ians|ees|ages|ers'))\s+(is|was|has|doesn't|isn't|wasn't)\b", lambda m: m.group(1) + " " + {"is": "are", "was": "were", "has": "have", "doesn't": "don't", "isn't": "aren't", "wasn't": "weren't"}[m.group(2).lower()], "agreement", "주어가 복수 명사(investors, companies, workers)이면 are / were / have / don't를 씁니다.")
rule(r"(?<!\band )(?<!\bor )\b([A-Z][a-z]+|[A-Z]{2,})\s+(have|haven't|don't|dont)\b(?! to\b)", lambda m: None if m.group(1).lower() in PLURAL_CAPS or m.group(1).endswith("s") else m.group(1) + " " + {"have": "has", "haven't": "hasn't", "don't": "doesn't", "dont": "doesn't"}[m.group(2).lower()], "agreement", "회사·사람 이름 같은 단수 주어(Nvidia, Apple, Tom)에는 has / doesn't를 씁니다.")
rule(r"\b(the|this|that|my|our|his|her|its|your|their) ((?:[a-z]+|[A-Z]{2,}) )?(?!(?:people|police|staff|team|government|family|media|data|public|children|crew|majority)\b)([a-z]{3,}?[^s\W]) (look|seem|need|want|make|go|become|cause|mean|depend|show|remain|affect|feel|work|happen|matter|cost|grow|keep|help)\b(?! (?:to|like)\b(?<=to\b))", lambda m: None if m.group(3) in STOP_SUBJ or m.group(3) in AGREE_VERBS or (m.group(2) or "").strip().lower() in STOP_SUBJ | COLLECTIVE else m.group(0)[: -len(m.group(4))] + third_person(m.group(4)), "agreement", "단수 주어(the boom, my company)의 현재형 동사에는 -s를 붙입니다. (the boom looks like …)")
# Konglish
rule(r"\bfighting!?", "Good luck! / You've got this!", "word_choice", "응원의 '화이팅'은 영어로 Good luck! / You can do it! 입니다. fighting은 '싸움'이라는 뜻이에요.", False)
rule(r"\beye[- ]?shopping\b", "window-shopping", "word_choice", "구경만 하는 쇼핑은 window-shopping입니다.")
rule(r"\bskinship\b", "physical affection", "word_choice", "skinship은 콩글리시입니다. physical affection / physical contact.")
rule(r"\bhand ?phones?\b", lambda m: "cell phone" + ("s" if m.group(0).lower().endswith("s") else ""), "word_choice", "handphone은 콩글리시입니다. cell phone / mobile phone / smartphone.")
rule(r"\bSNS\b", "social media", "word_choice", "SNS는 영어권에서 잘 쓰지 않습니다. social media.", True, 0)
rule(r"\bmy apart\b", "my apartment", "word_choice", "아파트는 apartment(미)/flat(영)입니다. apart는 '떨어져'라는 부사예요.")
rule(r"\b(go|went|going|goes) to (?:the )?health\b", lambda m: m.group(1) + " to the gym", "word_choice", "'헬스장'은 the gym입니다. health는 '건강'이에요.")
rule(r"\b(arbeit|arbite|arbaito)\b", "part-time job", "word_choice", "아르바이트는 part-time job입니다.")
rule(r"\bmy condition (?:is|was) (?:not good|bad|terrible)\b", "I'm not feeling well", "word_choice", "'컨디션이 안 좋다'는 I'm not feeling well / I'm under the weather가 자연스럽습니다.")
rule(r"\bmy mental\b", "my mental health", "word_choice", "mental은 형용사라 혼자 명사로 쓰지 않습니다. my mental health / my mind.")
rule(r"\b(good|bad) manner\b", r"\1 manners", "word_choice", "'예의'라는 뜻일 때는 복수형 manners를 씁니다.")
rule(r"\b(cunning)\b(?= (?:on|in) (?:the )?(?:test|exam))", "cheating", "word_choice", "시험 부정행위는 cheating입니다. cunning은 '교활한'이에요.")
# punctuation & mechanics
rule(r"(?<![\w'’])i(?=['’]m\b|['’]ve\b|['’]ll\b|['’]d\b|(?![\w'’]))", "I", "capitalization", "1인칭 I는 항상 대문자로 씁니다.", True, 0)
rule(r"\b(\w+)\s+\1\b", lambda m: None if m.group(1).lower() in ("had", "that", "is") else m.group(1), "repetition", "같은 단어가 두 번 반복됐습니다.")
rule(r" +([,.!?;:])", r"\1", "punctuation", "쉼표·마침표 앞에는 띄어쓰지 않습니다.", True, 0)
rule(r"([,;!?])(?=[A-Za-z])", r"\1 ", "punctuation", "쉼표·물음표 뒤에는 한 칸 띄웁니다.", True, 0)
rule(r"(?<=[a-z]{2})\.(?=[A-Z][a-z])", ". ", "punctuation", "마침표 뒤에는 한 칸 띄웁니다.", True, 0)
rule(r"(?<=\S)  +(?=\S)", " ", "punctuation", "띄어쓰기가 두 칸 이상입니다.", True, 0)
rule(r"\b(" + "|".join(MISSPELL) + r")\b", lambda m: keep_case(m.group(1), MISSPELL[m.group(1).lower()]), "spelling", "철자 오류입니다.")


def _article_rule(text):
    out = []
    for m in re.finditer(r"\b([Aa]n?) ([A-Za-z][\w-]*)", text):
        art, w = m.group(1), m.group(2)
        lw = w.lower()
        if w.isupper() and len(w) > 1:  # acronyms: an FBI agent, a NATO summit
            vowel_sound = lw[0] in "aefhilmnorsx" and not lw.startswith(("u",))
            if lw[0] in "aeio" and len(w) > 3 and w not in ("NASA", "NATO", "OPEC"):
                vowel_sound = True
            if w in ("NASA", "NATO", "OPEC"):
                vowel_sound = False
        else:
            vowel_sound = lw[0] in "aeiou"
            if lw.startswith(AN_EXCEPT_CONSONANT_SOUND):
                vowel_sound = False
            if lw.startswith(AN_EXCEPT_VOWEL_SOUND):
                vowel_sound = True
        want = "an" if vowel_sound else "a"
        if art.lower() != want:
            new = keep_case(art, want)
            out.append(_issue(m.start(1), m.end(1), art, new, "article",
                              f"'{w}'는 {'모음' if vowel_sound else '자음'} 소리로 시작해서 '{want}'를 씁니다. (철자가 아니라 발음 기준)", True))
    return out


def _third_person_rule(text):
    out = []
    for m in re.finditer(r"\b(he|she|it|this|that|the company|the government|my boss|my friend|everyone|everybody|someone|somebody|nobody|no one|anyone|each)\s+(" + "|".join(BASE_VERBS) + r")\b", text, re.I):
        before = text[:m.start()].rstrip().split()
        if before and before[-1].lower().strip(",.") in MODALS:
            continue
        verb = m.group(2)
        new = third_person(verb.lower())
        out.append(_issue(m.start(2), m.end(2), verb, new, "agreement",
                          f"3인칭 단수 주어({m.group(1)}) 현재형에는 동사에 -s를 붙입니다. ({verb} → {new})", True))
    return out


def _sentence_rules(text):
    out = []
    pos = 0
    sents = sentences(text)
    for idx, s in enumerate(sents):
        start = text.find(s, pos)
        if start < 0:
            continue
        pos = start + len(s)
        first = re.match(r"[\"“']?([a-z])", s)
        if first:
            st = start + first.start(1)
            out.append(_issue(st, st + 1, s[first.start(1)], s[first.start(1)].upper(), "capitalization",
                              "문장의 첫 글자는 대문자로 씁니다.", True))
        n = len(words(s))
        if n > 35:
            out.append(_issue(start, pos, s, None, "structure",
                              f"한 문장이 {n}단어로 너무 깁니다. 접속사(and, but, because) 앞에서 두 문장으로 나누면 읽기 쉬워요.", False))
        if re.match(r"\s*Because\b", s) and "," not in s and n < 15:
            out.append(_issue(start, pos, s, None, "structure",
                              "Because로 시작하는 절만 있고 주절이 없습니다(불완전한 문장). 앞 문장과 연결하거나 주절을 붙이세요.", False))
        if re.search(r"\b(yesterday|last (?:week|month|year|night|friday|monday|weekend)|\d+ (?:days|weeks|months|years) ago|this morning)\b", s, re.I):
            for mv in re.finditer(r"\b(I|we|they|you|he|she|it|my \w+|the \w+) (go|goes|is|am|are|have|has|see|sees|come|comes|get|gets|take|takes|buy|buys|meet|meets|eat|eats|feel|feels|think|thinks|say|says|tell|tells|find|finds|hear|hears|read|reads|watch|watches)\b", s):
                past = {"go": "went", "goes": "went", "is": "was", "am": "was", "are": "were", "have": "had", "has": "had",
                        "see": "saw", "sees": "saw", "come": "came", "comes": "came", "get": "got", "gets": "got",
                        "take": "took", "takes": "took", "buy": "bought", "buys": "bought", "meet": "met", "meets": "met",
                        "eat": "ate", "eats": "ate", "feel": "felt", "feels": "felt", "think": "thought", "thinks": "thought",
                        "say": "said", "says": "said", "tell": "told", "tells": "told", "find": "found", "finds": "found",
                        "hear": "heard", "hears": "heard", "read": "read", "reads": "read", "watch": "watched", "watches": "watched"}
                v = mv.group(2)
                vs = start + mv.start(2)
                out.append(_issue(vs, vs + len(v), v, past[v], "tense",
                                  f"과거 시점(yesterday, last week, ago)이 있는 문장이라 과거형이 맞습니다. ({v} → {past[v]})", True))
        # although/though ... but
        if re.search(r"\b(although|though|even though)\b", s, re.I) and re.search(r",\s*but\b", s, re.I):
            mm = re.search(r",\s*but\b", s, re.I)
            out.append(_issue(start + mm.start(), start + mm.end(), mm.group(0), ",", "structure",
                              "although와 but을 한 문장에 같이 쓰지 않습니다. 둘 중 하나만 쓰세요.", True))
    stripped = text.rstrip()
    if stripped and stripped[-1] not in ".!?\"”')":
        out.append(_issue(len(stripped), len(stripped), "", ".", "punctuation", "문장 끝에 마침표를 찍어 주세요.", True))
    return out


def _style_rules(text):
    out = []
    for m in re.finditer(r"\b(very|really|so) (" + "|".join(sorted(VERY_UPGRADE, key=len, reverse=True)) + r")\b", text, re.I):
        up = VERY_UPGRADE[m.group(2).lower()]
        out.append(_issue(m.start(), m.end(), m.group(0), keep_case(m.group(0), up), "style",
                          f"'{m.group(0)}' 대신 한 단어 '{up}'를 쓰면 더 힘 있고 자연스럽습니다.", False))
    low = text.lower()
    n_think = len(re.findall(r"\bi think\b", low))
    if n_think >= 3:
        out.append(_issue(0, 0, "", None, "style",
                          f"'I think'를 {n_think}번 썼습니다. In my view / I believe / It seems to me / I'd argue that 등으로 바꿔 보세요.", False))
    n_lot = len(re.findall(r"\ba lot of\b", low))
    if n_lot >= 2:
        out.append(_issue(0, 0, "", None, "style",
                          f"'a lot of'를 {n_lot}번 썼습니다. many / numerous / a great deal of / plenty of로 다양하게 써 보세요.", False))
    n_thing = len(re.findall(r"\bthings?\b", low))
    if n_thing >= 2:
        out.append(_issue(0, 0, "", None, "style",
                          "'thing'은 막연한 단어입니다. issue, factor, problem, decision처럼 구체적인 명사를 써 보세요.", False))
    for w in ("good", "bad", "big"):
        c = len(re.findall(r"\b" + w + r"\b", low))
        if c >= 3:
            alts = {"good": "beneficial, positive, impressive, solid", "bad": "harmful, damaging, disappointing, worrying",
                    "big": "major, significant, massive, substantial"}[w]
            out.append(_issue(0, 0, "", None, "style", f"'{w}'를 {c}번 썼습니다. 대신 {alts} 같은 단어를 써 보세요.", False))
    return out


def _issue(start, end, original, corrected, typ, ko, autofix, source="rule"):
    return {"start": start, "end": end, "original": original, "corrected": corrected, "type": typ,
            "explanation_ko": ko, "autofix": bool(autofix and corrected is not None), "source": source}


_WORDLIST = None


def _load_wordlist(path):
    global _WORDLIST
    if _WORDLIST is None:
        _WORDLIST = set()
        if path and os.path.exists(path):
            with open(path, encoding="utf-8", errors="ignore") as fh:
                _WORDLIST = {ln.strip().lower() for ln in fh if ln.strip()}
    return _WORDLIST


def _edits1(w):
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(w[:i], w[i:]) for i in range(len(w) + 1)]
    return {a + b[1:] for a, b in splits if b} | {a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1} | \
           {a + c + b[1:] for a, b in splits if b for c in letters} | {a + c + b for a, b in splits for c in letters}


def _spell_rules(text, wordlist_path, extra_known):
    wl = _load_wordlist(wordlist_path)
    if not wl:
        return []
    out = []
    for m in re.finditer(r"\b[a-z]{4,}\b", text):  # lowercase only: skip names and acronyms
        w = m.group(0)
        if w in wl or w in extra_known or w in MISSPELL:
            continue
        base_forms = {w[:-1], w[:-2], w[:-3], w[:-2] + "e", w[:-3] + "e", w[:-3] + "y", w[:-1] + "e"}
        if any(b in wl for b in base_forms if len(b) > 2):
            continue
        cands = sorted(c for c in _edits1(w) if c in wl)
        out.append(_issue(m.start(), m.end(), w, cands[0] if len(cands) == 1 else None, "spelling",
                          "사전에 없는 단어입니다. 철자를 확인하세요." + (f" 혹시: {', '.join(cands[:4])}" if cands else ""),
                          len(cands) == 1))
    return out


def _languagetool(text, cfg):
    url = cfg.get("url") or "https://api.languagetool.org/v2/check"
    data = urllib.parse.urlencode({"text": text, "language": cfg.get("language", "en-US")}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as r:
            res = json.loads(r.read().decode())
    except Exception:
        return []
    cat_map = {"TYPOS": "spelling", "GRAMMAR": "grammar", "PUNCTUATION": "punctuation", "STYLE": "style",
               "COLLOCATIONS": "collocation", "CONFUSED_WORDS": "word_choice", "CASING": "capitalization",
               "REDUNDANCY": "awkward", "TYPOGRAPHY": "punctuation", "SEMANTICS": "word_choice"}
    out = []
    for mt in res.get("matches", []):
        s, l = mt["offset"], mt["length"]
        reps = [r["value"] for r in mt.get("replacements", [])[:3]]
        typ = cat_map.get(mt.get("rule", {}).get("category", {}).get("id", ""), "grammar")
        out.append(_issue(s, s + l, text[s:s + l], reps[0] if reps else None, typ,
                          "[LanguageTool] " + mt.get("message", ""), typ not in ("style",), "languagetool"))
    return out


TYPE_KO = {"grammar": "문법", "agreement": "수 일치", "tense": "시제", "article": "관사", "preposition": "전치사",
           "collocation": "연어(단어 궁합)", "word_choice": "단어 선택", "structure": "문장 구조", "awkward": "어색한 표현",
           "style": "더 나은 표현", "spelling": "철자", "punctuation": "구두점·띄어쓰기", "capitalization": "대문자",
           "repetition": "반복"}
CATEGORY = {"grammar": "grammar", "agreement": "grammar", "tense": "grammar", "article": "grammar",
            "preposition": "grammar", "spelling": "grammar", "punctuation": "mechanics", "capitalization": "mechanics",
            "repetition": "mechanics", "collocation": "naturalness", "word_choice": "naturalness",
            "structure": "naturalness", "awkward": "naturalness", "style": "style"}


def _collect(text, config, known_words):
    issues = []
    for pat, repl, typ, ko, autofix in R:
        for m in pat.finditer(text):
            if callable(repl):
                new = repl(m)
                if new is None:
                    continue
            elif repl is None:
                new = None
            else:
                new = m.expand(repl)
                if not pat.flags & re.I or typ in ("punctuation",):
                    pass
                new = keep_case(m.group(0), new) if typ not in ("punctuation", "capitalization") else new
            if new is not None and new == m.group(0):
                continue
            issues.append(_issue(m.start(), m.end(), m.group(0), new, typ, ko, autofix))
    issues += _article_rule(text) + _third_person_rule(text) + _sentence_rules(text) + _style_rules(text)
    issues += _spell_rules(text, config.get("wordlist_path"), set(known_words))
    lt = config.get("languagetool", {})
    if lt.get("enabled"):
        issues += _languagetool(text, lt)

    # resolve overlaps: earlier rules win; zero-width global notes always kept
    kept, taken = [], []
    for it in issues:
        if it["type"] == "capitalization":
            if any(k["type"] == "capitalization" and k["start"] == it["start"] for k in kept):
                continue
            kept.append(it)
            continue
        if it["start"] == it["end"] == 0 and it["original"] == "":
            kept.append(it)
            continue
        span = (it["start"], max(it["end"], it["start"] + 1))
        if any(not (span[1] <= a or span[0] >= b) for a, b in taken):
            continue
        taken.append(span)
        kept.append(it)
    kept.sort(key=lambda x: (x["start"], x["end"]))
    for it in kept:
        it["type_ko"] = TYPE_KO.get(it["type"], it["type"])
        it["category"] = CATEGORY.get(it["type"], "grammar")

    return kept


def check(text, config=None, known_words=()):
    config = config or {}
    kept = _collect(text, config, known_words)
    corrected = apply(text, [i for i in kept if i["autofix"]])
    # fixing one error can reveal another hidden under it ("thousands flights was" -> "thousands of flights was"):
    # re-check the corrected text up to twice and add what is new
    for _ in range(2):
        more = [i for i in _collect(corrected, config, known_words)
                if i["autofix"] and i["type"] not in ("capitalization", "punctuation") and i["original"]]
        if not more:
            break
        kept += more
        corrected = apply(corrected, more)
    polished = corrected
    style = [i for i in _collect(corrected, config, known_words) if i["type"] == "style" and i["corrected"]]
    if style:
        polished = apply(corrected, style)
    return {"issues": kept, "corrected": corrected, "polished": polished}


def apply(text, issues):
    """Apply replacements from the end backwards; capitalization is redone afterwards on the result."""
    out = text
    caps = any(i["type"] == "capitalization" for i in issues)
    for it in sorted(issues, key=lambda x: -x["start"]):
        if it["corrected"] is None or it["type"] == "capitalization":
            continue
        out = out[: it["start"]] + it["corrected"] + out[it["end"]:]
    if caps:
        out = re.sub(r"(?<![\w'’])i(?=['’](?:m|ve|ll|d)\b|(?![\w'’]))", "I", out)
        out = re.sub(r"(^\s*|[.!?][\"”')]*\s+)([\"“']?)([a-z])", lambda m: m.group(1) + m.group(2) + m.group(3).upper(), out)
    out = re.sub(r"\.\.$", ".", out.rstrip())
    return out
