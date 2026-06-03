#!/usr/bin/env python3
"""
Bloomberg Japan RSS Generator
Fetches Bloomberg Japan articles via Google News RSS and publishes as feed.xml.
"""

import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import datetime
import re
import sys
import os

GNEWS_URL = (
    "https://news.google.com/rss/search"
    "?q=site:bloomberg.com/jp&hl=ja&gl=JP&ceid=JP:ja"
)
OUTPUT_FILE = "feed.xml"
MAX_ITEMS = 50

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
    "Accept-Language": "ja,en;q=0.9",
}


def fetch_gnews(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_gnews(data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    items = []
    for item_el in root.findall(".//item"):
        title_el = item_el.find("title")
        link_el = item_el.find("link")
        pubdate_el = item_el.find("pubDate")

        if title_el is None or link_el is None:
            continue

        # Strip " - Bloomberg.com" suffix from title
        title = (title_el.text or "").strip()
        title = re.sub(r"\s*-\s*Bloomberg\.com\s*$", "", title)

        link = (link_el.text or "").strip()
        pubdate = (pubdate_el.text or "").strip() if pubdate_el is not None else ""

        items.append({"title": title, "link": link, "pubdate": pubdate})

    return items[:MAX_ITEMS]


def build_rss(items: list[dict]) -> str:
    now_rfc = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    def escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
        )

    item_parts = []
    for item in items:
        pub = item["pubdate"] or now_rfc
        item_parts.append(
            f"""    <item>
      <title>{escape(item['title'])}</title>
      <link>{escape(item['link'])}</link>
      <guid isPermaLink="false">{escape(item['link'])}</guid>
      <pubDate>{pub}</pubDate>
    </item>"""
        )

    items_xml = "\n".join(item_parts)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ブルームバーグ日本語版 最新ニュース</title>
    <link>https://www.bloomberg.com/jp</link>
    <description>Bloomberg.com/jp の最新日本語ニュース（非公式フィード）</description>
    <language>ja</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <ttl>30</ttl>
{items_xml}
  </channel>
</rss>
"""


def main():
    print(f"Fetching Bloomberg Japan articles from Google News ...")
    try:
        data = fetch_gnews(GNEWS_URL)
    except urllib.error.HTTPError as e:
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing ({len(data)} bytes) ...")
    items = parse_gnews(data)
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
