#!/usr/bin/env python3
"""Build the web version's data (runs daily on GitHub Actions — no AI).

  python build_site.py                    # fetch today's news from RSS and update docs/
  python build_site.py --offline sample   # build from the sample feeds (for testing, no internet)

Output
  docs/data/<date>.json   one day's ranking, briefing, passages, questions, vocabulary
  docs/data/index.json    list of available days
  docs/data/glossary.json your my_glossary.tsv as JSON
  docs/py/core/*.py       the same Python code, run in the browser (Pyodide) for corrections and reports
"""
import argparse
import datetime as dt
import glob
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from core import feeds, pipeline, vocab  # noqa: E402
from core.textutil import truncate_words  # noqa: E402

BROWSER_MODULES = ["__init__", "textutil", "glossary", "rank", "digest", "vocab", "questions", "grammar",
                   "scoring", "report", "pipeline"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", help="folder with sample RSS files instead of the internet")
    ap.add_argument("--out", default=os.path.join(BASE, "docs"))
    ap.add_argument("--keep-days", type=int, default=60)
    a = ap.parse_args()

    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
        config = json.load(fh)
    tz = dt.timezone(dt.timedelta(hours=config.get("timezone_offset_hours", 9)))
    date = dt.datetime.now(tz).date().isoformat()
    offline = os.path.join(BASE, a.offline) if a.offline else None

    print(f"[{date}] 뉴스 수집 ({'예시 파일' if offline else 'RSS'})")
    items = pipeline.dedupe(feeds.fetch_all(config, offline))
    if not items:
        sys.exit("가져온 기사가 없습니다. 피드 주소나 네트워크를 확인하세요.")
    # a public website must not republish whole articles: by default the web version uses only RSS summaries
    if not offline and config.get("web_fetch_full_text", False):
        feeds.add_full_text(items, config)
    now = max(dt.datetime.fromisoformat(i["published"]) for i in items) + dt.timedelta(hours=1) if offline else None
    user_g = vocab.load_user_glossary(BASE)
    day = pipeline.build_day_data(items, date, config, dict(pipeline.DEFAULT_SETTINGS), now=now, user_g=user_g,
                                  offline=bool(offline))

    # keep the top stories with trimmed article text, so the browser can rebuild passages for other settings
    day["stories"] = day["stories"][:30]
    for s in day["stories"]:
        for art in s["articles"]:
            art["body"] = truncate_words(art.get("body") or "", 400)
        s.pop("rep_text", None)
    day["stories_lite"] = pipeline.lite_stories(day)

    data_dir = os.path.join(a.out, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, f"{date}.json"), "w", encoding="utf-8") as fh:
        json.dump(day, fh, ensure_ascii=False)
    with open(os.path.join(data_dir, "glossary.json"), "w", encoding="utf-8") as fh:
        json.dump(user_g, fh, ensure_ascii=False)

    # index + cleanup
    files = sorted(glob.glob(os.path.join(data_dir, "20??-??-??.json")), reverse=True)
    for old in files[a.keep_days:]:
        os.remove(old)
    index = []
    for f in files[: a.keep_days]:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        index.append({"date": d["date"], "n_items": d["n_items"], "outlets": d["outlets"],
                      "top": d["stories"][0]["title"] if d["stories"] else "", "offline": d.get("offline", False)})
    with open(os.path.join(data_dir, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"updated": dt.datetime.now(tz).isoformat(timespec="minutes"), "days": index}, fh, ensure_ascii=False)

    # python code for the browser
    py_dir = os.path.join(a.out, "py", "core")
    os.makedirs(py_dir, exist_ok=True)
    for m in BROWSER_MODULES:
        shutil.copy(os.path.join(BASE, "core", m + ".py"), os.path.join(py_dir, m + ".py"))
    print(f"완료: 기사 {day['n_items']}건, 이야기 {len(day['stories'])}개, 지문 {len(day['passages'])}개 → {data_dir}")


if __name__ == "__main__":
    main()
