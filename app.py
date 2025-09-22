# app.py
import os, json, re, asyncio, datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime

import httpx
from fastapi import FastAPI, Query
from bs4 import BeautifulSoup
import feedparser

# ------------ Settings ------------
UA = "Encaptechno-TrendBot/1.0"
TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT", "15"))
DEFAULT_CONC = int(os.getenv("MAX_CONCURRENCY", "8"))

try:
    import h2  # noqa: F401
    HTTP2_AVAILABLE = True
except Exception:
    HTTP2_AVAILABLE = False

# ------------ Embedded urls.json ------------
SOURCES_EMBEDDED: List[Dict[str, Any]] = [
  {
    "source": "Google News RSS (Search)",
    "category": "news",
    "endpoint": "https://news.google.com/rss/search?q=(d2c%20OR%20%22direct-to-consumer%22%20OR%20%22direct%20to%20consumer%22)%20AND%20(ecommerce%20OR%20brand)%20when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    "method": "GET",
    "format": "xml",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "GDELT Docs API",
    "category": "news",
    "endpoint": "https://api.gdeltproject.org/api/v2/doc/doc?query=d2c%20OR%20%22direct-to-consumer%22%20OR%20%22direct%20to%20consumer%22%20AND%20(ecommerce%20OR%20brand)%20sourceCountry:IN&timespan=7d&mode=ArtList&maxrecords=250&format=json",
    "method": "GET",
    "format": "json",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "Reddit r/IndiaStartups",
    "category": "social",
    "endpoint": "https://www.reddit.com/r/IndiaStartups/search.json?q=d2c%20OR%20%22direct-to-consumer%22&restrict_sr=1&sort=new&t=week",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "Reddit r/ecommerce",
    "category": "social",
    "endpoint": "https://www.reddit.com/r/ecommerce/search.json?q=d2c%20OR%20%22direct-to-consumer%22&restrict_sr=1&sort=new&t=week",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "Hacker News (Algolia)",
    "category": "tech_news",
    "endpoint": "https://hn.algolia.com/api/v1/search_by_date?query=%22direct-to-consumer%22%20OR%20D2C&tags=story",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "YouTube Search Feed",
    "category": "video",
    "endpoint": "https://www.youtube.com/feeds/videos.xml?search_query=d2c+india+ecommerce",
    "method": "GET",
    "format": "atom",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "Google Trends Daily",
    "category": "search_trend",
    "endpoint": "https://trends.google.com/trends/api/dailytrends?hl=en-IN&tz=330&geo=IN",
    "method": "GET",
    "format": "json",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "Apple App Store RSS (Top Free)",
    "category": "apps",
    "endpoint": "https://itunes.apple.com/in/rss/topfreeapplications/limit=50/genre=6024/json",
    "method": "GET",
    "format": "json",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "Apple App Store RSS (Top Grossing)",
    "category": "apps",
    "endpoint": "https://itunes.apple.com/in/rss/topgrossingapplications/limit=50/genre=6024/json",
    "method": "GET",
    "format": "json",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "Yahoo Finance Trending Tickers",
    "category": "markets",
    "endpoint": "https://query1.finance.yahoo.com/v1/finance/trending/IN?lang=en-IN&region=IN",
    "method": "GET",
    "format": "json",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "GitHub Repo Search",
    "category": "dev",
    "endpoint": "https://api.github.com/search/repositories?q=ecommerce+OR+d2c+created:%3E2025-09-01&sort=stars&order=desc&per_page=50",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "npm Registry Search",
    "category": "dev",
    "endpoint": "https://registry.npmjs.org/-/v1/search?text=ecommerce%20OR%20d2c&size=50&popularity=1.0",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "OpenAlex Works",
    "category": "research",
    "endpoint": "https://api.openalex.org/works?search=%22direct-to-consumer%22%20OR%20d2c%20ecommerce&sort=publication_date:desc&per_page=50",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  },
  {
    "source": "Amazon Movers & Shakers (IN)",
    "category": "commerce",
    "endpoint": "https://www.amazon.in/gp/movers-and-shakers",
    "method": "GET",
    "format": "html",
    "region": "IN",
    "auth_required": False
  },
  {
    "source": "Wikipedia Pageviews: Direct-to-consumer",
    "category": "knowledge_trend",
    "endpoint": "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Direct-to-consumer/daily/20250101/20251231",
    "method": "GET",
    "format": "json",
    "region": "Global",
    "auth_required": False
  }
]

# ------------ Core ------------
class SourceObj:
    def __init__(self, **kw):
        self.source: str = kw.get("source")
        self.category: Optional[str] = kw.get("category")
        self.endpoint: str = kw["endpoint"]
        self.method: str = kw.get("method", "GET")
        self.format: Optional[str] = kw.get("format")
        self.region: Optional[str] = kw.get("region")
        self.auth_required: Optional[bool] = kw.get("auth_required", False)
        self.notes: Optional[str] = kw.get("notes")
        self.placeholders: Optional[Dict[str, str]] = kw.get("placeholders")

def _load_sources(file: Optional[str]) -> List[SourceObj]:
    if file and os.path.isfile(file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [SourceObj(**x) for x in data]
    return [SourceObj(**x) for x in SOURCES_EMBEDDED]

def _strip_json_xssi(text: str) -> str:
    return re.sub(r"^\)\]\}',?\s*", "", text)

def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc.lower()
    except Exception:
        return ""

def _now_iso() -> str:
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

def _to_iso(ts: Any) -> Optional[str]:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        sec = ts / 1000.0 if ts > 2_000_000_000 else ts
        try:
            return datetime.datetime.utcfromtimestamp(sec).replace(tzinfo=datetime.timezone.utc).isoformat()
        except Exception:
            return None
    if isinstance(ts, str):
        s = ts.strip()
        if re.fullmatch(r"\d{14}", s):
            try:
                return datetime.datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc).isoformat()
            except Exception:
                pass
        if re.fullmatch(r"\d{10,13}", s):
            try:
                return _to_iso(int(s))
            except Exception:
                pass
        try:
            dt = parsedate_to_datetime(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc).isoformat()
        except Exception:
            pass
        try:
            return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(datetime.timezone.utc).isoformat()
        except Exception:
            return None
    return None

_POS = {"rise", "growth", "record", "expand", "funding", "profit"}
_NEG = {"decline", "fall", "loss", "slowdown", "layoff", "ban"}

def _headline_sentiment(text: Optional[str]) -> Dict[str, float]:
    t = (text or "").lower()
    pos_n = sum(1 for w in _POS if w in t)
    neg_n = sum(1 for w in _NEG if w in t)
    matches = pos_n + neg_n
    if matches == 0:
        return {"magnitude": 0.0, "score": 0.0}
    score = (pos_n - neg_n) / matches
    return {"magnitude": float(matches), "score": round(score, 2)}

def _parse_xml(text: str) -> Dict[str, Any]:
    feed = feedparser.parse(text)
    items = []
    for e in feed.entries[:200]:
        items.append({
            "title": e.get("title"),
            "link": (e.get("link") or (e.links[0]["href"] if e.get("links") else None)),
            "published": e.get("published") or e.get("updated"),
            "summary": e.get("summary"),
            "author": (getattr(e, "author", None) or (e.get("authors", [{}])[0].get("name") if e.get("authors") else None)),
            "media_thumbnail": (e.get("media_thumbnail", [{}])[0].get("url") if e.get("media_thumbnail") else None),
        })
    return {"items": items}

def _parse_html(text: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    return {"title": title, "url": url}

def _parse_json_by_domain(url: str, payload: Any) -> Dict[str, Any]:
    d = _domain(url)
    try:
        if "gdeltproject.org" in d:
            arts = payload.get("articles") or payload.get("results") or []
            items = [{
                "title": a.get("title"),
                "url": a.get("url"),
                "seen": a.get("seendate") or a.get("date"),
                "source": a.get("domain") or a.get("sourceCommonName"),
                "summary": a.get("snippet"),
            } for a in arts]
            return {"items": items[:200]}
        if "reddit.com" in d:
            children = payload.get("data", {}).get("children", [])
            items = [{
                "title": c.get("data", {}).get("title"),
                "url": "https://www.reddit.com" + (c.get("data", {}).get("permalink") or ""),
                "created_utc": c.get("data", {}).get("created_utc"),
                "author": c.get("data", {}).get("author"),
                "selftext": c.get("data", {}).get("selftext"),
                "subreddit": c.get("data", {}).get("subreddit"),
            } for c in children]
            return {"items": items}
        if "algolia.com" in d:  # HN search
            hits = payload.get("hits", [])
            items = [{
                "title": h.get("title") or h.get("story_title"),
                "url": h.get("url") or h.get("story_url"),
                "created_at": h.get("created_at"),
                "author": h.get("author"),
                "summary": h.get("story_text") or h.get("comment_text"),
            } for h in hits]
            return {"items": items}
        if "trends.google.com" in d:
            days = payload.get("default", {}).get("trendingSearchesDays", [])
            items = []
            for day in days:
                for t in day.get("trendingSearches", []):
                    for a in t.get("articles", []):
                        items.append({
                            "title": a.get("title"),
                            "url": a.get("url"),
                            "published": a.get("timeAgo"),
                            "source": a.get("source"),
                        })
            return {"items": items}
        if "apple.com" in d or "itunes.apple.com" in d:
            feed = payload.get("feed", {})
            results = feed.get("results", [])
            items = [{
                "title": r.get("name"),
                "url": r.get("url"),
                "author": r.get("artistName"),
            } for r in results]
            return {"items": items}
        if "api.github.com" in d:
            items = payload.get("items", [])
            return {"items": [{
                "title": it.get("full_name"),
                "url": it.get("html_url"),
                "created_at": it.get("created_at"),
                "author": it.get("owner", {}).get("login"),
                "summary": it.get("description"),
            } for it in items]}
        if "registry.npmjs.org" in d:
            objs = payload.get("objects", [])
            return {"items": [{
                "title": o.get("package", {}).get("name"),
                "url": o.get("package", {}).get("links", {}).get("npm"),
                "created_at": o.get("package", {}).get("date"),
                "summary": o.get("package", {}).get("description"),
                "author": (o.get("package", {}).get("publisher") or {}).get("username"),
            } for o in objs]}
        if "openalex.org" in d:
            works = payload.get("results", [])
            return {"items": [{
                "title": w.get("title"),
                "url": (w.get("primary_location") or {}).get("source", {}).get("homepage_url")
                        or (w.get("primary_location") or {}).get("landing_page_url"),
                "created_at": w.get("publication_date"),
                "author": (w.get("authorships", [{}])[0].get("author", {}).get("display_name") if w.get("authorships") else None),
                "summary": w.get("abstract_inverted_index") and " ".join(w.get("abstract_inverted_index").keys()),
            } for w in works]}
        if "wikimedia.org" in d:
            return {"items": []}
    except Exception:
        pass
    return {"json": payload}

async def _fetch_one(client: httpx.AsyncClient, src: SourceObj) -> Dict[str, Any]:
    url = src.endpoint
    try:
        r = await client.get(url, headers={"User-Agent": UA, "Accept": "*/*"})
        ct = r.headers.get("content-type", "").lower()
        body_text = r.text
        if "trends.google.com" in url and body_text.lstrip().startswith(")]}'"):
            body_text = _strip_json_xssi(body_text)
            data = json.loads(body_text)
            parsed = _parse_json_by_domain(url, data)
        elif "json" in ct or url.lower().endswith(".json"):
            data = r.json()
            parsed = _parse_json_by_domain(url, data)
        elif "xml" in ct or "rss" in ct or body_text.strip().startswith("<?xml") or "<feed" in body_text:
            parsed = _parse_xml(body_text)
        elif "html" in ct:
            parsed = _parse_html(body_text, url)
        else:
            try:
                data = r.json()
                parsed = _parse_json_by_domain(url, data)
            except Exception:
                parsed = {"text": body_text[:2000]}
        return {"src": src, "status": r.status_code, "content_type": ct, "parsed": parsed}
    except Exception as e:
        return {"src": src, "status": "error", "error": str(e), "parsed": {}}

def _source_name_from_item(item: Dict[str, Any], endpoint: str) -> str:
    if isinstance(item.get("source"), str) and item.get("source"):
        return item["source"]
    if item.get("link"):
        return _domain(item["link"])
    if item.get("url"):
        return _domain(item["url"])
    d = _domain(endpoint)
    if "reddit" in d: return "reddit"
    if "algolia" in d: return "Hacker News"
    if "gdelt" in d: return "GDELT"
    if "youtube" in d: return "YouTube"
    return d or "unknown"

def _first_nonempty(*vals):
    for v in vals:
        if v not in (None, "", [], {}):
            return v
    return None

def _norm_one(item: Dict[str, Any], endpoint: str) -> Optional[Dict[str, Any]]:
    title = _first_nonempty(item.get("title"), item.get("name"))
    url = _first_nonempty(item.get("url"), item.get("link"))
    published_raw = _first_nonempty(
        item.get("published"),
        item.get("updated"),
        item.get("created_at"),
        item.get("created_utc"),
        item.get("seen"),
        item.get("date"),
    )
    published_iso = _to_iso(published_raw)
    author = _first_nonempty(item.get("author"), item.get("artistName"))
    description = _first_nonempty(item.get("summary"), item.get("selftext"))
    url_to_image = _first_nonempty(item.get("urlToImage"), item.get("media_thumbnail"))
    content = item.get("content")
    if not title or not url:
        return None
    source_name = _source_name_from_item(item, endpoint)
    sentiment = _headline_sentiment(title)
    return {
        "title": title,
        "source": {"name": source_name},
        "author": author,
        "url": url,
        "publishedAt": published_iso,
        "description": description,
        "urlToImage": url_to_image,
        "content": content,
        "language": "en",
        "documentSentiment": {
            "magnitude": float(sentiment["magnitude"]),
            "score": float(sentiment["score"]),
        },
    }

def _dedupe(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        key = (it.get("url") or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out

async def _run(file: Optional[str], limit_per_source: int, concurrent: int, require_published: bool) -> List[Dict[str, Any]]:
    sources = _load_sources(file)
    limits = httpx.Limits(max_keepalive_connections=concurrent, max_connections=concurrent)
    timeout = httpx.Timeout(TIMEOUT_S)
    sem = asyncio.Semaphore(concurrent)
    async with httpx.AsyncClient(timeout=timeout, limits=limits, http2=HTTP2_AVAILABLE) as client:
        async def bounded_fetch(s: SourceObj):
            async with sem:
                return await _fetch_one(client, s)
        fetched = await asyncio.gather(*(bounded_fetch(s) for s in sources))
    items: List[Dict[str, Any]] = []
    for r in fetched:
        src: SourceObj = r.get("src")
        parsed = r.get("parsed") or {}
        raw_items = (parsed.get("items") if isinstance(parsed, dict) else None) or []
        if isinstance(raw_items, list):
            for it in raw_items[:limit_per_source]:
                norm = _norm_one(it, src.endpoint)
                if not norm:
                    continue
                if require_published and not norm.get("publishedAt"):
                    continue
                items.append(norm)
    return _dedupe(items)

# ------------ API ------------
app = FastAPI(title="D2C Trend Fetcher", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True, "ts": _now_iso(), "http2": HTTP2_AVAILABLE}

@app.get("/sources")
def get_sources(file: Optional[str] = Query(None, description="Optional external urls.json; defaults to embedded")):
    return _load_sources(file)

@app.get("/feed")
async def feed(
    file: Optional[str] = Query(None, description="Optional external urls.json; defaults to embedded"),
    limit_per_source: int = Query(50, ge=1, le=200),
    concurrent: int = Query(DEFAULT_CONC, ge=1, le=32),
    require_published: bool = Query(True),
):
    items = await _run(file, limit_per_source, concurrent, require_published)
    return {"fetched_at": _now_iso(), "count": len(items), "items": items}

@app.get("/trends")
async def trends(
    file: Optional[str] = Query(None),
    limit_per_source: int = Query(20, ge=0, le=200),
    concurrent: int = Query(DEFAULT_CONC, ge=1, le=32),
):
    # Per-source raw parse for debugging
    sources = _load_sources(file)
    limits = httpx.Limits(max_keepalive_connections=concurrent, max_connections=concurrent)
    timeout = httpx.Timeout(TIMEOUT_S)
    sem = asyncio.Semaphore(concurrent)
    async with httpx.AsyncClient(timeout=timeout, limits=limits, http2=HTTP2_AVAILABLE) as client:
        async def bounded_fetch(s: SourceObj):
            async with sem:
                return await _fetch_one(client, s)
        results = await asyncio.gather(*(bounded_fetch(s) for s in sources))
    # Trim items lists
    for r in results:
        parsed = r.get("parsed")
        if isinstance(parsed, dict) and isinstance(parsed.get("items"), list) and limit_per_source > 0:
            parsed["items"] = parsed["items"][:limit_per_source]
    return {"fetched_at": _now_iso(), "count": len(results), "results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
