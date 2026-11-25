#!/usr/bin/env python3
"""데일리 외신 영어 — AI 없이 돌아가는 로컬 버전.

  python app.py            # 서버 실행 후 브라우저 열기 (http://localhost:8765)
  python app.py fetch      # 지금 뉴스만 수집해서 저장 (작업 스케줄러/cron 용)
  python app.py demo       # 인터넷 없이 sample/ 폴더의 예시 피드로 체험

Python 3.9+ 표준 라이브러리만 사용합니다. 설치할 패키지가 없습니다.
"""
import argparse
import datetime as dt
import json
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from core import feeds, rank, vocab, scoring, report, pipeline  # noqa: E402
from core.pipeline import DEFAULT_SETTINGS  # noqa: E402
from core.store import Store  # noqa: E402


with open(os.path.join(BASE, "config.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)
STORE = Store(os.path.join(BASE, "data", "newsdesk.db"))
FETCH = {"running": False, "log": [], "last_error": None}


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    FETCH["log"] = (FETCH["log"] + [line])[-60:]


def today():
    return dt.date.today().isoformat()


# ---------------------------------------------------------------------------------------- pipeline
def make_passages(day, settings):
    return pipeline.make_passages(day, settings, vocab.load_user_glossary(BASE))


def build_day(date, offline_dir=None):
    log(f"뉴스 수집 시작 ({'오프라인 예시' if offline_dir else '인터넷 RSS'})")
    items = pipeline.dedupe(feeds.fetch_all(CONFIG, offline_dir, log))
    if not items:
        raise RuntimeError("가져온 기사가 없습니다. 인터넷 연결이나 config.json의 피드 주소를 확인하세요.")
    if not offline_dir:
        log("기사 본문 앞부분 가져오는 중…")
        feeds.add_full_text(items, CONFIG, log)
    now = None
    if offline_dir:  # sample feeds have fixed dates: rank them as if it were their own day
        now = max(dt.datetime.fromisoformat(i["published"]) for i in items) + dt.timedelta(hours=1)
    day = pipeline.build_day_data(items, date, CONFIG, STORE.get_settings(DEFAULT_SETTINGS), now=now,
                                  user_g=vocab.load_user_glossary(BASE), offline=bool(offline_dir))
    log(f"기사 {len(items)}건 → 같은 사건끼리 묶어 {len(day['stories'])}개 이야기로 정리")
    STORE.save_day(date, day)
    log(f"완료: 브리핑 1편, 지문 {len(day['passages'])}개, 단어 {len(day['vocab'])}개")
    return day


def run_fetch_async(offline_dir=None):
    if FETCH["running"]:
        return False

    def job():
        FETCH["running"], FETCH["last_error"], FETCH["log"] = True, None, []
        try:
            build_day(today(), offline_dir)
        except Exception as e:
            FETCH["last_error"] = str(e)
            log("오류: " + str(e))
        finally:
            FETCH["running"] = False

    threading.Thread(target=job, daemon=True).start()
    return True


def scheduler():
    """While the server is running, fetch once a day at daily_fetch_time."""
    last = None
    while True:
        hh, mm = map(int, CONFIG.get("daily_fetch_time", "07:00").split(":"))
        now = dt.datetime.now()
        if now.hour == hh and now.minute == mm and last != now.date():
            last = now.date()
            run_fetch_async()
        time.sleep(30)


# ---------------------------------------------------------------------------------------- HTTP API
def day_payload(date):
    day = STORE.get_day(date)
    if not day:
        return None
    ans = STORE.answers(date)
    grouped = {}
    for a in ans:
        grouped.setdefault(f"p{a['pi']}q{a['qi']}", []).append(
            {"id": a["id"], "text": a["text"], "mode": a["mode"], "feedback": a["feedback"], "at": a["created_at"]})
    lite = dict(day)
    lite["stories"] = pipeline.lite_stories(day)
    lite["answers"] = grouped
    return lite


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path in ("/", "/index.html"):
            with open(os.path.join(BASE, "static", "index.html"), "rb") as fh:
                return self._send(200, fh.read(), "text/html; charset=utf-8")
        if u.path == "/api/state":
            return self._send(200, {"days": STORE.list_days(), "today": today(),
                                    "settings": STORE.get_settings(DEFAULT_SETTINGS),
                                    "fetch": {"running": FETCH["running"], "log": FETCH["log"][-12:],
                                              "error": FETCH["last_error"]},
                                    "config": {"daily_fetch_time": CONFIG.get("daily_fetch_time"),
                                               "languagetool": CONFIG["checker"]["languagetool"]["enabled"],
                                               "outlets": sorted({f["outlet"] for f in CONFIG["feeds"] if f.get("enabled", True)})}})
        if u.path == "/api/day":
            d = day_payload(q.get("date", today()))
            return self._send(200 if d else 404, d or {"error": "no day"})
        if u.path == "/api/report":
            days = [STORE.get_day(d) for d in STORE.list_days()]
            return self._send(200, report.build_report(STORE.answers(), [d for d in days if d],
                                                       STORE.get_settings(DEFAULT_SETTINGS)))
        if u.path == "/api/words":
            return self._send(200, STORE.words())
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            b = self._body()
        except json.JSONDecodeError:
            return self._send(400, {"error": "bad json"})
        if u.path == "/api/fetch":
            started = run_fetch_async(os.path.join(BASE, "sample") if b.get("offline") else None)
            return self._send(200, {"started": started})
        if u.path == "/api/settings":
            allowed = {k: b[k] for k in DEFAULT_SETTINGS if k in b}
            STORE.set_settings(allowed)
            return self._send(200, STORE.get_settings(DEFAULT_SETTINGS))
        if u.path == "/api/regenerate":
            date = b.get("date", today())
            day = STORE.get_day(date)
            if not day:
                return self._send(404, {"error": "no day"})
            STORE.delete_answers(date)
            make_passages(day, STORE.get_settings(DEFAULT_SETTINGS))
            STORE.save_day(date, day)
            return self._send(200, day_payload(date))
        if u.path == "/api/answer":
            day = STORE.get_day(b["date"])
            text = (b.get("text") or "").strip()
            if not day or not text:
                return self._send(400, {"error": "날짜나 답변이 비어 있습니다."})
            p = day["passages"][int(b["pi"])]
            qq = p["questions"][int(b["qi"])]
            fb = scoring.assess(text, p, qq, b.get("mode", "typed"), CONFIG, STORE.get_settings(DEFAULT_SETTINGS))
            aid = STORE.add_answer({"date": b["date"], "pi": int(b["pi"]), "qi": int(b["qi"]), "question": qq["q"],
                                    "qtype": qq["type"], "passage_title": p["title"], "category": p["category"],
                                    "text": text, "mode": b.get("mode", "typed"), "feedback": fb})
            return self._send(200, {"id": aid, "feedback": fb})
        if u.path == "/api/words":
            act, term = b.get("action"), b.get("term", "")
            if act == "star":
                STORE.star(term, b.get("ko", ""), b.get("example", ""), b.get("date", today()))
            elif act == "unstar":
                STORE.unstar(term)
            elif act in ("known", "unknown"):
                STORE.mark_word(term, act == "known")
            return self._send(200, STORE.words())
        return self._send(404, {"error": "not found"})


def main():
    ap = argparse.ArgumentParser(description="데일리 외신 영어 (AI 없는 로컬 버전)")
    ap.add_argument("command", nargs="?", default="serve", choices=["serve", "fetch", "demo"])
    ap.add_argument("--port", type=int, default=CONFIG.get("port", 8765))
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    if a.command == "fetch":
        build_day(today())
        return
    if a.command == "demo":
        build_day(today(), os.path.join(BASE, "sample"))
    elif CONFIG.get("auto_fetch_on_start") and today() not in STORE.list_days():
        run_fetch_async()

    threading.Thread(target=scheduler, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    url = f"http://localhost:{a.port}"
    print(f"\n  데일리 외신 영어 실행 중 → {url}\n  끝내려면 Ctrl+C\n", flush=True)
    if not a.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("종료합니다.")


if __name__ == "__main__":
    main()
