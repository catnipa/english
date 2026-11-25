"""Fetching news from official RSS feeds and (optionally) the article page text.

Only the Python standard library is used. No AI.
"""
import datetime as dt
import email.utils
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

from .textutil import clean_html, word_count

UA = "Mozilla/5.0 (personal English-study reader; +https://localhost)"


def http_get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        d = None
    if d is None:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc)


def _strip_ns(tag):
    return tag.split("}", 1)[-1]


def parse_feed(xml_text, feed):
    """Parse RSS 2.0 or Atom. Returns list of item dicts."""
    xml_text = re.sub(r"^[^<]+", "", xml_text)
    root = ET.fromstring(xml_text)
    items = []
    nodes = [n for n in root.iter() if _strip_ns(n.tag) in ("item", "entry")]
    for pos, node in enumerate(nodes):
        f = {}
        for ch in node:
            t = _strip_ns(ch.tag)
            if t == "link":
                f["link"] = (ch.text or "").strip() or ch.attrib.get("href", "")
            elif t in ("title", "description", "summary", "pubDate", "published", "updated", "date", "encoded"):
                f.setdefault(t, "".join(ch.itertext()))
            elif t == "source":
                f["source"] = (ch.text or "").strip()
        title = clean_html(f.get("title", ""))
        if not title:
            continue
        outlet = feed["outlet"]
        if feed.get("strip_suffix"):
            title = re.sub(r"\s+[-–|]\s+" + re.escape(feed["strip_suffix"]) + r"\s*$", "", title)
        desc = clean_html(f.get("description") or f.get("summary") or f.get("encoded") or "")
        if feed.get("google_news"):
            desc = ""  # Google News descriptions only repeat the headline
        items.append({
            "outlet": outlet,
            "feed": feed.get("name", outlet),
            "feed_category": feed.get("category", ""),
            "title": title,
            "link": f.get("link", ""),
            "description": desc,
            "published": (_parse_date(f.get("pubDate") or f.get("published") or f.get("updated") or f.get("date")) or
                          dt.datetime.now(dt.timezone.utc)).isoformat(),
            "position": pos,
        })
    return items


class _ParaExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "aside", "figure", "figcaption", "header", "form", "noscript", "button"}

    def __init__(self):
        super().__init__()
        self.paras, self._buf, self._in_p, self._skip = [], [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "p":
            self._in_p += 1
            self._buf = []

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "p" and self._in_p:
            self._in_p -= 1
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.paras.append(text)

    def handle_data(self, data):
        if self._in_p and not self._skip:
            self._buf.append(data)


JUNK = re.compile(r"(subscribe|sign up|newsletter|all rights reserved|cookie|advertisement|click here|"
                  r"download the app|follow us|copyright|getty images|this story has been|contributed to this report)",
                  re.I)


def extract_article_text(html, max_words=600):
    p = _ParaExtractor()
    try:
        p.feed(html)
    except Exception:
        return ""
    good = [x for x in p.paras if word_count(x) >= 12 and not JUNK.search(x)]
    out, n = [], 0
    for para in good:
        out.append(para)
        n += word_count(para)
        if n >= max_words:
            break
    return "\n\n".join(out)


def fetch_all(config, offline_dir=None, log=print):
    """Fetch every enabled feed. Returns list of items."""
    feeds = [f for f in config["feeds"] if f.get("enabled", True)]
    items = []

    def one(feed):
        try:
            if offline_dir:
                path = os.path.join(offline_dir, feed["offline_file"]) if feed.get("offline_file") else None
                if not path or not os.path.exists(path):
                    return feed, [], "no offline file"
                with open(path, encoding="utf-8") as fh:
                    xml_text = fh.read()
            else:
                xml_text = http_get(feed["url"])
            return feed, parse_feed(xml_text, feed)[: config.get("max_items_per_feed", 25)], None
        except Exception as e:  # network or XML problems should never stop the whole run
            return feed, [], str(e)

    with ThreadPoolExecutor(max_workers=8) as ex:
        for feed, got, err in ex.map(one, feeds):
            if err:
                log(f"  ! {feed['name']}: {err}")
            else:
                log(f"  · {feed['name']}: {len(got)}건")
            items.extend(got)
    return items


def add_full_text(items, config, log=print):
    """Optionally download article pages and keep the opening paragraphs (for personal study)."""
    if not config.get("fetch_full_text", True):
        return
    targets = [it for it in items if it.get("link") and "news.google.com" not in it["link"]
               and it["outlet"] not in set(config.get("no_full_text_outlets", []))]

    def one(it):
        try:
            it["body"] = extract_article_text(http_get(it["link"], timeout=10), config.get("body_max_words", 600))
        except Exception:
            it["body"] = ""
        return it

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(one, targets))
    log(f"  · 본문 확보: {sum(1 for t in targets if t.get('body'))}/{len(targets)}건")
