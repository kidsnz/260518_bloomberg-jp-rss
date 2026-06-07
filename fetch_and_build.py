#!/usr/bin/env python3
"""
Bloomberg Japan RSS Generator (Yahoo! News edition)

Fetches Bloomberg Japan articles from the Yahoo! News media page
(news.yahoo.co.jp/media/bloom_st) and publishes them as feed.xml.

Each <link> points to the Yahoo! News article page, which remains
readable for free even though Bloomberg.com/jp itself is now paywalled.

The previous implementation that sourced articles via Google News RSS
(and linked to Bloomberg.com) is kept for reference at
archive/fetch_and_build_googlenews.py.
"""

import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

MEDIA_URL = "https://news.yahoo.co.jp/media/bloom_st"
MEDIA_LINK = MEDIA_URL  # channel <link>
OUTPUT_FILE = "feed.xml"
MAX_ITEMS = 50
PER_PAGE = 25  # Yahoo returns 25 items per page

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


def fetch_page(page: int) -> str:
    url = MEDIA_URL if page == 1 else f"{MEDIA_URL}?page={page}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_preloaded_state(html: str) -> dict:
    """Extract window.__PRELOADED_STATE__ via brace matching (robust to
    trailing scripts) and return it as a dict."""
    marker = "window.__PRELOADED_STATE__"
    i = html.find(marker)
    if i == -1:
        raise ValueError("__PRELOADED_STATE__ not found")
    start = html.find("{", i)
    if start == -1:
        raise ValueError("state object start not found")

    depth = 0
    in_str = False
    escape = False
    for j in range(start, len(html)):
        c = html[j]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(html[start:j + 1])
    raise ValueError("unbalanced state object")


def to_rfc822(dt: datetime.datetime) -> str:
    return (
        f"{_WDAY[dt.weekday()]}, {dt.day:02d} {_MON[dt.month - 1]} {dt.year} "
        f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} +0900"
    )


def article_datetime(entry: dict, now: datetime.datetime) -> str:
    """Best-effort publish time in RFC822 (+0900).

    Year is taken from the thumbnail URL (which embeds YYYYMMDD) when
    available; otherwise it is inferred from dateString relative to now.
    """
    hour = minute = 0
    tm = re.match(r"(\d{1,2}):(\d{2})", entry.get("timeString", "") or "")
    if tm:
        hour, minute = int(tm.group(1)), int(tm.group(2))

    # Prefer the date embedded in the thumbnail URL: /amd-img/YYYYMMDD-...
    thumb = entry.get("thumbUrl", "") or ""
    tu = re.search(r"/amd-img/(\d{4})(\d{2})(\d{2})-", thumb)
    if tu:
        year, month, day = int(tu.group(1)), int(tu.group(2)), int(tu.group(3))
        try:
            return to_rfc822(datetime.datetime(year, month, day, hour, minute, tzinfo=JST))
        except ValueError:
            pass

    # Fall back to dateString "M/D(曜)" with inferred year.
    dm = re.match(r"(\d{1,2})/(\d{1,2})", entry.get("dateString", "") or "")
    if dm:
        month, day = int(dm.group(1)), int(dm.group(2))
        try:
            dt = datetime.datetime(now.year, month, day, hour, minute, tzinfo=JST)
        except ValueError:
            return to_rfc822(now)
        # If the date lands in the future, it belongs to the previous year.
        if dt > now + datetime.timedelta(days=2):
            dt = dt.replace(year=now.year - 1)
        return to_rfc822(dt)

    return to_rfc822(now)


def collect_items() -> list[dict]:
    now = datetime.datetime.now(JST)
    items: list[dict] = []
    page = 1
    while len(items) < MAX_ITEMS:
        html = fetch_page(page)
        state = extract_preloaded_state(html)
        entries = state.get("mediaArticleList", {}).get("list", [])
        if not entries:
            break
        for e in entries:
            if e.get("isPay"):
                continue  # skip paywalled-on-Yahoo articles
            link = (e.get("newsLink") or "").strip()
            title = (e.get("headline") or "").strip()
            if not link or not title:
                continue
            items.append({
                "title": title,
                "link": link,
                "pubdate": article_datetime(e, now),
            })
            if len(items) >= MAX_ITEMS:
                break
        if len(entries) < PER_PAGE:
            break  # last page
        page += 1
    return items


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
      <pubDate>{item['pubdate']}</pubDate>
    </item>"""
        )

    items_xml = "\n".join(item_parts)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ブルームバーグ日本語版 最新ニュース</title>
    <link>{MEDIA_LINK}</link>
    <description>Yahoo!ニュースで配信中のブルームバーグ日本語版記事（非公式フィード）</description>
    <language>ja</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <ttl>30</ttl>
{items_xml}
  </channel>
</rss>
"""


def main():
    print("Fetching Bloomberg Japan articles from Yahoo! News ...")
    try:
        items = collect_items()
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error building feed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(items)} articles.")
    if not items:
        print("WARNING: No articles found.", file=sys.stderr)

    rss = build_rss(items)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
