"""Text utilities: tokenizing, sentence splitting, light lemmatizing, word lists.

Everything here is deterministic (rules + word lists). No machine learning.
"""
import math
import re
from collections import Counter

STOPWORDS = set("""
a about above after again against all almost also although am among an and any are aren't around as at
be because been before being below between both but by can can't cannot could couldn't did didn't do does
doesn't doing don't down during each either else even ever every few for from further get gets got had hadn't
has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's however
i i'd i'll i'm i've if in into is isn't it it's its itself just let's like many may me might more most much must
mustn't my myself neither no nor not now of off on once one only or other ought our ours ourselves out over own
per perhaps quite rather really said same say says shall shan't she she'd she'll she's should shouldn't since so
some still such than that that's the their theirs them themselves then there there's these they they'd they'll
they're they've this those though through thus to too toward towards under until up upon us very via was wasn't
we we'd we'll we're we've were weren't what what's whatever when when's where where's whether which while who
who's whom whose why why's will with within without won't would wouldn't yet you you'd you'll you're you've your
yours yourself yourselves amid amongst onto across along beside besides beyond despite inside outside unlike
mr mrs ms dr st new news year years week weeks day days time times told tell says said according including
""".split())

# Roughly the most frequent ~900 English words (everyday vocabulary). Words NOT in this list
# (and not stopwords) are treated as "advanced" for vocabulary extraction and scoring.
COMMON = set("""
able accept across act action activity actually add address admit adult affect afraid again age ago agree ahead
air allow alone already always amount animal another answer anyone anything appear apply area argue arm army
arrive art article ask attack attention away baby back bad bag ball bank bar base basic beat beautiful become bed
begin behind believe benefit best better big bill bit black blood blue board body book born boy break bring
brother build building business buy call camera campaign cancer candidate capital car card care career carry case
catch cause cell center central century certain chair challenge chance change character charge check child
choice choose church citizen city civil claim class clear clearly close coach cold collection college color come
commercial common community company compare computer concern condition conference consider consumer contain
continue control cost country couple course court cover create crime cultural culture cup current customer cut
dark data daughter dead deal death debate decade decide decision deep defense degree democrat describe design
detail determine develop development die difference different difficult dinner direction director discover
discuss discussion disease doctor dog door draw dream drive drop drug early east easy eat economic economy
edge education effect effort eight election else employee end energy enjoy enough enter entire environment
especially establish evening event everybody everyone everything evidence exactly example executive exist expect
experience expert explain eye face fact factor fail fall family far fast father fear federal feel feeling field
fight figure fill film final finally financial find fine finger finish fire firm first fish five floor fly focus
follow food foot force foreign forget form former forward four free friend front full fund future game garden gas
general generation girl give glass go goal good government great green ground group grow growth guess gun guy hair
half hand hang happen happy hard head health hear heart heat heavy help high himself history hit hold home hope
hospital hot hotel hour house huge human hundred husband idea identify image imagine impact important improve
include increase indeed indicate individual industry information inside instead institution interest interesting
international interview investment involve issue item job join keep key kid kill kind kitchen know knowledge land
language large last late later laugh law lawyer lay lead leader learn least leave left leg legal less letter level
lie life light likely line list listen little live local long look lose loss lot love low machine magazine main
maintain major majority make man manage management manager market marriage material matter maybe mean measure
media medical meet meeting member memory mention message method middle military million mind minute miss mission
model modern moment money month morning mother mouth move movement movie music myself name nation national
natural nature near nearly necessary need network never nice night none north note nothing notice number occur
offer office officer official often oil ok old open operation opportunity option order organization others
outside owner page pain painting paper parent part participant particular particularly partner party pass past
patient pattern pay peace people perform performance period person personal phone physical pick picture piece
place plan plant play player point police policy political politics poor popular population position positive
possible power practice prepare present president pressure pretty prevent price private probably problem process
produce product production professional professor program project property protect prove provide public pull
purpose push put question quickly race radio raise range rate reach read ready real reality realize reason receive
recent recently recognize record red reduce reflect region relate relationship religious remain remember remove
report represent republican require research resource respond response rest result return reveal rich right rise
risk road rock role room rule run safe save scene school science scientist score sea season seat second section
security see seek seem sell send senior sense series serious serve service set seven several sex shake share shoot
short shot show side sign significant similar simple simply sing single sister sit site situation six size skill
skin small smile social society soldier somebody someone something sometimes son song soon sort sound source
south southern space speak special specific speech spend sport spring staff stage stand standard star start state
statement station stay step stock stop store story strategy street strong structure student study stuff style
subject success successful suddenly suffer suggest summer support sure surface system table take talk task tax
teach teacher team technology television ten tend term test thank thing think third thousand threat three
throughout throw today together tonight top total tough town trade traditional training travel treat treatment
tree trial trip trouble true truth try turn tv two type understand unit up use usually value various victim view
violence visit voice vote wait walk wall want war watch water way weapon wear weight well west western whatever
white whole wide wife win wind window wish woman wonder word work worker world worry write writer wrong yard yeah
yes young yourself
afternoon airport angry answered apartment asked bad believe bike birthday bored boring bread breakfast brown busy
cake cat cheap cheese chicken children clean clothes coffee cook cool cousin crazy cry dance dangerous dear delicious
dress drink dry egg email english exam excited expensive famous fantastic farm fat favorite fit flower fruit funny
gift glad gold guitar happy hat hello holiday homework hungry ice internet job juice kitchen lazy lunch milk mom
dad nervous noisy orange party pen pencil photo pink pizza plane poor quiet rain rainy restaurant rice salad sad
sandwich scared shirt shoe shop shopping sick sleep slow snow sorry soup student sugar sun sunny sweet swim tea
terrible tired toy train ugly vacation weather weekend wet wonderful yellow
""".split())

PARTICLES = {"up", "down", "out", "off", "back", "over", "in", "on", "away", "through", "around"}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*[A-Za-z]|[A-Za-z]")
ABBREV = {"mr.", "mrs.", "ms.", "dr.", "st.", "u.s.", "u.k.", "e.g.", "i.e.", "inc.", "corp.", "co.", "jan.", "feb.",
          "aug.", "sept.", "sep.", "oct.", "nov.", "dec.", "gov.", "sen.", "rep.", "vs.", "no.", "jr.", "sr.", "ltd."}


def words(text):
    return WORD_RE.findall(text or "")


def sentences(text):
    """Split into sentences, keeping common abbreviations together."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    parts, buf = [], []
    for tok in text.split(" "):
        buf.append(tok)
        low = tok.lower()
        if re.search(r"[.!?][\"'”’)]*$", tok) and low not in ABBREV and not re.fullmatch(r"[A-Z]\.", tok):
            parts.append(" ".join(buf))
            buf = []
    if buf:
        parts.append(" ".join(buf))
    return [p.strip() for p in parts if p.strip()]


def lemma(w):
    """Very small rule-based lemmatizer (good enough for matching word lists)."""
    w = w.lower().strip("'-")
    if len(w) <= 3:
        return w
    irregular = {"went": "go", "gone": "go", "was": "be", "were": "be", "has": "have", "had": "have", "did": "do",
                 "done": "do", "made": "make", "said": "say", "took": "take", "taken": "take", "came": "come",
                 "saw": "see", "seen": "see", "got": "get", "gave": "give", "given": "give", "found": "find",
                 "thought": "think", "told": "tell", "became": "become", "left": "leave", "felt": "feel",
                 "brought": "bring", "began": "begin", "kept": "keep", "held": "hold", "wrote": "write",
                 "stood": "stand", "heard": "hear", "meant": "mean", "met": "meet", "ran": "run", "paid": "pay",
                 "sat": "sit", "spoke": "speak", "led": "lead", "grew": "grow", "lost": "lose", "fell": "fall",
                 "sent": "send", "built": "build", "rose": "rise", "risen": "rise", "sold": "sell", "bought": "buy",
                 "children": "child", "people": "person", "men": "man", "women": "woman", "fled": "flee",
                 "struck": "strike", "won": "win", "hit": "hit", "cut": "cut", "shut": "shut", "spent": "spend"}
    if w in irregular:
        return irregular[w]
    for suf, rep in (("ies", "y"), ("ied", "y")):
        if w.endswith(suf) and len(w) > 4:
            return w[:-3] + rep
    if w.endswith("sses") or w.endswith("shes") or w.endswith("ches") or w.endswith("xes") or w.endswith("zes"):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is", "os")):
        return w[:-1]
    if w.endswith("ing") and len(w) > 5:
        base = w[:-3]
        if len(base) > 2 and base[-1] == base[-2] and base[-1] not in "lsz":
            return base[:-1]
        if base + "e" in COMMON:
            return base + "e"
        return base
    if w.endswith("ed") and len(w) > 4:
        base = w[:-2]
        if len(base) > 2 and base[-1] == base[-2] and base[-1] not in "lsz":
            return base[:-1]
        if base + "e" in COMMON or w[:-1] in COMMON:
            return w[:-1]
        return base
    return w


def is_common(w):
    lw = w.lower()
    return lw in STOPWORDS or lw in COMMON or lemma(lw) in COMMON or lemma(lw) in STOPWORDS


def keywords(text):
    """Content keywords (lemmatized, stopwords removed)."""
    out = []
    for w in words(text):
        lw = w.lower()
        if lw in STOPWORDS or len(lw) < 3 or lw.isdigit():
            continue
        out.append(lemma(lw))
    return out


def proper_nouns(text):
    """Capitalized word sequences that are not at sentence start (rough named entities)."""
    ents = set()
    for sent in sentences(text):
        toks = words(sent)
        i = 0
        while i < len(toks):
            t = toks[i]
            if t[0].isupper() and (i > 0 or len(toks) == 1) and t.lower() not in STOPWORDS:
                j = i
                while j + 1 < len(toks) and toks[j + 1][0].isupper():
                    j += 1
                ents.add(" ".join(toks[i:j + 1]))
                i = j + 1
            else:
                i += 1
    return ents


def tfidf_vectors(docs):
    """docs: list of keyword lists. Returns list of dict vectors (L2-normalized)."""
    df = Counter()
    for d in docs:
        df.update(set(d))
    n = len(docs) or 1
    vecs = []
    for d in docs:
        tf = Counter(d)
        v = {t: (1 + math.log(c)) * math.log(1 + n / df[t]) for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(t, 0.0) for t, x in a.items())


def clean_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&rsquo;", "’").replace("&lsquo;", "‘")
          .replace("&ldquo;", "“").replace("&rdquo;", "”").replace("&mdash;", "—").replace("&ndash;", "–"))
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
    return re.sub(r"\s+", " ", s).strip()


def word_count(text):
    return len(words(text))


def truncate_words(text, n):
    """First n words, cut at a sentence end when possible."""
    out, count = [], 0
    for s in sentences(text):
        c = word_count(s)
        if count and count + c > n:
            break
        out.append(s)
        count += c
        if count >= n:
            break
    return " ".join(out)
