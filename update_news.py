#!/usr/bin/env python3
"""Build news.json from public RSS feeds. Uses only Python standard library."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json, re, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "news.json"
FEEDS = [
    ("Anime News Network", "https://www.animenewsnetwork.com/news/rss.xml?ann-edition=us", "anime"),
    ("Variety", "https://variety.com/v/film/feed/", "movies"),
    ("Variety", "https://variety.com/v/tv/feed/", "tv"),
    ("The Hollywood Reporter", "https://www.hollywoodreporter.com/feed/", "general"),
]
NS = {"media": "http://search.yahoo.com/mrss/", "content": "http://purl.org/rss/1.0/modules/content/", "atom": "http://www.w3.org/2005/Atom"}

def clean_html(value, limit=360):
    value = unescape(value or "")
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].rstrip() + ("…" if len(value) > limit else "")

def child_text(node, names):
    for name in names:
        if ":" in name:
            prefix, local = name.split(":", 1)
            uri = NS.get(prefix)
            found = node.find(f"{{{uri}}}{local}") if uri else None
        else:
            found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def parse_date(value):
    if not value:
        return ""
    try:
        d = parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except Exception:
        try:
            d = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except Exception:
            return ""

def item_image(item):
    for path in ("media:content", "media:thumbnail", "enclosure"):
        el = item.find(path, NS) if ":" in path else item.find(path)
        if el is not None:
            url = el.attrib.get("url", "")
            if url.startswith("https://") or url.startswith("http://"):
                return url
    encoded = item.find("content:encoded", NS)
    blob = encoded.text if encoded is not None else ""
    if not blob:
        desc = item.find("description")
        blob = desc.text if desc is not None else ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', blob or "", re.I)
    if m and m.group(1).startswith(("https://", "http://")):
        return m.group(1)
    return ""

def classify(title, summary, default):
    text = (title + " " + summary).lower()
    if default == "anime" or any(k in text for k in ("anime", "manga", "japanese animation", "voice actor", "crunchyroll")):
        return "anime"
    if default in ("movies", "tv"):
        return default
    if any(k in text for k in ("tv series", "television", "streaming series", "showrunner", "season finale", "episode order", "tv show", "series premiere", "limited series")):
        return "tv"
    if any(k in text for k in ("film", "movie", "box office", "cinema", "feature directorial", "theatrical release", "filmmaker")):
        return "movies"
    return "movies"

def parse_feed(source, url, default_category):
    req = Request(url, headers={"User-Agent": "WatchTimeNewsFeed/1.0 (+https://github.com/)"})
    with urlopen(req, timeout=25) as response:
        payload = response.read()
    root = ET.fromstring(payload)
    nodes = root.findall(".//item")
    if not nodes:
        nodes = root.findall(".//atom:entry", NS)
    out = []
    for node in nodes:
        title = clean_html(child_text(node, ["title", "atom:title"]), 220)
        link = child_text(node, ["link"])
        if not link:
            el = node.find("atom:link", NS)
            if el is not None: link = el.attrib.get("href", "")
        if link and not link.startswith(("https://", "http://")):
            continue
        summary = clean_html(child_text(node, ["description", "content:encoded", "summary", "atom:summary"]), 360)
        date = child_text(node, ["pubDate", "published", "updated", "atom:published", "atom:updated"])
        image = item_image(node)
        category = classify(title, summary, default_category)
        if title and link:
            out.append({"title": title, "link": link, "source": source, "published": parse_date(date), "summary": summary, "category": category, "image": image})
    return out

def main():
    items, errors = [], []
    for source, url, category in FEEDS:
        try:
            got = parse_feed(source, url, category)
            items.extend(got)
            print(f"{source} ({category}): {len(got)} stories")
        except Exception as exc:
            errors.append(f"{source}: {exc}")
            print(f"WARNING: {source} feed failed: {exc}")
    unique = {}
    for item in items:
        key = item["link"].split("#", 1)[0].rstrip("/")
        if key and key not in unique:
            unique[key] = item
    final = sorted(unique.values(), key=lambda x: x.get("published", ""), reverse=True)[:100]
    data = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "items": final, "feed_errors": errors}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(final)} unique stories to {OUT}")
    # Fail only when every source fails, so one unavailable publisher doesn't break updates.
    if not final:
        raise SystemExit("No stories were retrieved from any RSS feed")

if __name__ == "__main__":
    main()
