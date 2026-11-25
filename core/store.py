"""SQLite storage (one file: data/newsdesk.db)."""
import json
import os
import sqlite3
import threading
import datetime as dt

_lock = threading.Lock()


class Store:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with _lock:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS days(date TEXT PRIMARY KEY, data TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pi INTEGER, qi INTEGER,
                question TEXT, qtype TEXT, passage_title TEXT, category TEXT, text TEXT, mode TEXT,
                feedback TEXT, overall REAL, created_at TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS words(term TEXT PRIMARY KEY, ko TEXT, example TEXT, date TEXT, added_at TEXT,
                reviews INTEGER DEFAULT 0, known INTEGER DEFAULT 0);
            CREATE INDEX IF NOT EXISTS ans_date ON answers(date);
            """)
            self.db.commit()

    # days
    def save_day(self, date, data):
        with _lock:
            self.db.execute("REPLACE INTO days VALUES(?,?,?)", (date, json.dumps(data, ensure_ascii=False), now()))
            self.db.commit()

    def get_day(self, date):
        r = self.db.execute("SELECT data FROM days WHERE date=?", (date,)).fetchone()
        return json.loads(r["data"]) if r else None

    def list_days(self):
        return [r["date"] for r in self.db.execute("SELECT date FROM days ORDER BY date DESC")]

    # answers
    def add_answer(self, a):
        with _lock:
            cur = self.db.execute(
                "INSERT INTO answers(date,pi,qi,question,qtype,passage_title,category,text,mode,feedback,overall,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (a["date"], a["pi"], a["qi"], a["question"], a.get("qtype", ""), a.get("passage_title", ""),
                 a.get("category", ""), a["text"], a.get("mode", "typed"), json.dumps(a["feedback"], ensure_ascii=False),
                 a["feedback"]["overall"], now()))
            self.db.commit()
            return cur.lastrowid

    def answers(self, date=None):
        q = "SELECT * FROM answers" + (" WHERE date=?" if date else "") + " ORDER BY id"
        rows = self.db.execute(q, (date,) if date else ()).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["feedback"] = json.loads(d["feedback"])
            out.append(d)
        return out

    def delete_answers(self, date):
        with _lock:
            self.db.execute("DELETE FROM answers WHERE date=?", (date,))
            self.db.commit()

    # settings
    def get_settings(self, defaults):
        s = dict(defaults)
        for r in self.db.execute("SELECT key, value FROM settings"):
            s[r["key"]] = json.loads(r["value"])
        return s

    def set_settings(self, d):
        with _lock:
            for k, v in d.items():
                self.db.execute("REPLACE INTO settings VALUES(?,?)", (k, json.dumps(v)))
            self.db.commit()

    # word notebook
    def star(self, term, ko, example, date):
        with _lock:
            self.db.execute("INSERT OR IGNORE INTO words(term,ko,example,date,added_at) VALUES(?,?,?,?,?)",
                            (term, ko, example, date, now()))
            self.db.commit()

    def unstar(self, term):
        with _lock:
            self.db.execute("DELETE FROM words WHERE term=?", (term,))
            self.db.commit()

    def mark_word(self, term, known):
        with _lock:
            self.db.execute("UPDATE words SET known=?, reviews=reviews+1 WHERE term=?", (1 if known else 0, term))
            self.db.commit()

    def words(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM words ORDER BY known, added_at DESC")]


def now():
    return dt.datetime.now().isoformat(timespec="seconds")
