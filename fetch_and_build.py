#!/usr/bin/env python3
"""
Bloomberg Japan RSS Generator (TBS NEWS DIG edition)

Fetches the Bloomberg Japan article list published by TBS NEWS DIG
("TBS CROSS DIG with Bloomberg", an official partnership) and publishes
the headlines as feed.xml. Only headlines and links are included; each
<link> points to the free full-text article page on newsdig.tbs.co.jp.

Previous implementations are kept for reference:
  archive/fetch_and_build_yahoo.py        Yahoo! News (media/bloom_st), stopped 2026-10-01
  archive/fetch_and_build_googlenews.py   Google News RSS
"""

import datetime
import html
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE_URL = "https://newsdig.tbs.co.jp"
LIST_URL = f"{BASE_URL}/list/withbloomberg/news/bloomberg"
OUTPUT_FILE = "feed.xml"
MAX_ITEMS = 50
MAX_PAGES = 3  # 20 articles per page (plus a few extras that are de-duplicated)
# Category logo in the list: bb = Bloomberg, crossdig = CROSS DIG with Bloomberg.
# Other values (e.g. "dig") are TBS's own reporting and are not Bloomberg articles.
BLOOMBERG_CATS = {"bb", "crossdig"}

JST = datetime.timezone(datetime.timedelta(hours=9))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en;q=0.9",
}

_WDAY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_ARTICLE_RE = re.compile(r'<article class="m-article">(.*?)</article>', re.S)
_HREF_RE = re.compile(r'href="(/articles/withbloomberg/(\d+))[^"]*"')
_TIME_RE = re.compile(r'<time[^>]*datetime="([^"]+)"')
_TITLE_RE = re.compile(r'm-article__ttl">(.*?)</div>', re.S)
_CAT_RE = re.compile(r'/cat_(\w+)\.svg')


def fetch_page(page: int) -> str:
    url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
    req = urllib.request.Request(url, headers=HEADERS)
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last  # type: ignore[misc]


def parse_list(page_html: str) -> list[dict]:
    """Parse one list page. Raises ValueError if the page has no article
    blocks at all (layout change / error page), so a broken fetch never
    turns into an empty feed."""
    blocks = _ARTICLE_RE.findall(page_html)
    if not blocks:
        raise ValueError("no <article class=\"m-article\"> blocks found")
    items = []
    for b in blocks:
        href = _HREF_RE.search(b)
        tm = _TIME_RE.search(b)
        ttl = _TITLE_RE.search(b)
        cat = _CAT_RE.search(b)
        if not (href and tm and ttl and cat):
            continue
        if cat.group(1) not in BLOOMBERG_CATS:
            continue
        title = html.unescape(re.sub(r"<[^>]+>", "", ttl.group(1))).strip()
        if not title:
            continue
        items.append({
            "id": href.group(2),
            "title": title,
            "link": f"{BASE_URL}{href.group(1)}?display=1",
            "dt": datetime.datetime.fromisoformat(tm.group(1)),
        })
    return items


def to_rfc822(dt: datetime.datetime) -> str:
    dt = dt.astimezone(JST)
    return (
        f"{_WDAY[dt.weekday()]}, {dt.day:02d} {_MON[dt.month - 1]} {dt.year} "
        f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} +0900"
    )


def collect_items() -> list[dict]:
    seen: dict[str, dict] = {}
    now = datetime.datetime.now(JST)
    for page in range(1, MAX_PAGES + 1):
        for it in parse_list(fetch_page(page)):
            if it["dt"] > now + datetime.timedelta(hours=1):
                continue  # never publish a future-dated item
            seen.setdefault(it["id"], it)
    items = sorted(seen.values(), key=lambda x: x["dt"], reverse=True)
    return items[:MAX_ITEMS]


def build_rss(items: list[dict]) -> str:
    now_rfc = to_rfc822(datetime.datetime.now(JST))

    def escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
        )

    item_parts = []
    for item in items:
        item_parts.append(
            f"""    <item>
      <title>{escape(item['title'])}</title>
      <link>{escape(item['link'])}</link>
      <guid isPermaLink="true">{escape(item['link'])}</guid>
      <pubDate>{to_rfc822(item['dt'])}</pubDate>
    </item>"""
        )

    items_xml = "\n".join(item_parts)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ブルームバーグ日本語版 最新ニュース</title>
    <link>{LIST_URL}</link>
    <description>TBS NEWS DIG「TBS CROSS DIG with Bloomberg」で配信中のブルームバーグ日本語版記事の見出し（非公式フィード）</description>
    <language>ja</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <ttl>30</ttl>
{items_xml}
  </channel>
</rss>
"""


def main():
    print("Fetching Bloomberg Japan articles from TBS NEWS DIG ...")
    try:
        items = collect_items()
    except Exception as e:
        print(f"Error building feed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(items)} articles.")
    if not items:
        # Keep the previous feed.xml rather than overwrite it with an empty one.
        print("ERROR: No articles found; feed.xml left unchanged.", file=sys.stderr)
        sys.exit(1)

    rss = build_rss(items)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
