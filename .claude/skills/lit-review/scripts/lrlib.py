"""lit-review shared helpers: logging, HTTP with backoff, key loading, credit tracking.

Design: scripts do the mechanical I/O and write introspectable output to a RUN DIR so the
orchestrating LLM can poll files instead of re-running work. Everything logs to run.log
(timestamped, leveled) AND updates a machine-readable *_summary.json.
"""
import json, os, sys, time, random, re, threading, urllib.parse, datetime as dt
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed: pip install requests")

# ---------- keys (read at call time, never printed) ----------
OPENALEX_KEY_FILE = Path.home() / ".config" / "openalex.key"
S2_KEY_FILE = Path.home() / ".config" / "semantic-scholar-api.key"
MAILTO = "mail@denisalevi.de"

def _read_key(p):
    try:
        return p.read_text().strip() or None
    except Exception:
        return None

def openalex_key():  return _read_key(OPENALEX_KEY_FILE)
def s2_key():        return _read_key(S2_KEY_FILE)

# ---------- logging ----------
class Log:
    """Timestamped, leveled logger → run.log + stderr. Cheap to grep after the fact."""
    def __init__(self, run_dir):
        self.path = Path(run_dir) / "run.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a", buffering=1)  # line-buffered
    def _w(self, lvl, msg):
        line = f"{dt.datetime.now().isoformat(timespec='seconds')} {lvl:5} {msg}"
        self._fh.write(line + "\n")
        print(line, file=sys.stderr)
    def info(self, m):  self._w("INFO", m)
    def warn(self, m):  self._w("WARN", m)
    def error(self, m): self._w("ERROR", m)
    def ok(self, m):    self._w("OK", m)

# ---------- Retry-After parsing (numeric seconds OR HTTP-date) ----------
def _retry_after_seconds(ra):
    """Return seconds to wait from a Retry-After header, or None if unparseable.
    Handles both numeric ('120') and HTTP-date ('Wed, 21 Oct 2026 07:28:00 GMT') forms."""
    if not ra:
        return None
    ra = ra.strip()
    if ra.isdigit():
        return float(ra)
    try:
        from email.utils import parsedate_to_datetime
        when = parsedate_to_datetime(ra)
        if when is None:
            return None
        # tz-aware vs naive: compare in UTC
        nowdt = dt.datetime.now(when.tzinfo) if when.tzinfo else dt.datetime.now()
        return max(0.0, (when - nowdt).total_seconds())
    except Exception:
        return None

# ---------- Per-host rate limiter (shared across threads) ----------
class HostRateLimiter:
    """Thread-safe per-hostname minimum-interval gate. Lets many hosts run in parallel
    while keeping any single host (esp. Semantic Scholar) under its cumulative rate limit."""
    def __init__(self, default_interval=0.0, per_host=None):
        self.default = default_interval
        self.per_host = per_host or {}
        self._last = {}
        self._locks = {}
        self._guard = threading.Lock()
    def _host(self, url):
        try: return urllib.parse.urlparse(url).hostname or ""
        except Exception: return ""
    def wait(self, url):
        host = self._host(url)
        interval = self.per_host.get(host, self.default)
        if interval <= 0:
            return
        with self._guard:
            lock = self._locks.setdefault(host, threading.Lock())
        with lock:
            last = self._last.get(host, 0.0)
            gap = interval - (time.time() - last)
            if gap > 0:
                time.sleep(gap)
            self._last[host] = time.time()

# ---------- HTTP with backoff + rate limiting ----------
class Http:
    """GET/POST with 429/5xx exponential backoff + full jitter, Retry-After honored,
    and a minimum inter-request interval (self-throttle). Tracks request counts."""
    def __init__(self, log, min_interval=0.0, max_retries=5, base=1.0, cap=60.0, source="http",
                 host_limiter=None):
        self.log = log; self.min_interval = min_interval; self.max_retries = max_retries
        self.base = base; self.cap = cap; self.source = source
        self.host_limiter = host_limiter  # optional shared HostRateLimiter (per-host, thread-safe)
        self._last = 0.0; self.n_requests = 0; self.n_429 = 0
        self.s = requests.Session()
        self.s.headers["User-Agent"] = f"lit-review/1.0 (mailto:{MAILTO})"
    def _throttle(self, url=None):
        # per-host shared gate first (keeps S2 ≤1 req/s across all workers), then the local interval
        if self.host_limiter and url:
            self.host_limiter.wait(url)
        if self.min_interval:
            wait = self.min_interval - (time.time() - self._last)
            if wait > 0: time.sleep(wait)
    def request(self, method, url, headers=None, json_body=None, timeout=20):
        allow_redirects = method != "HEAD"  # HEAD: don't follow, a 3xx already proves existence
        for attempt in range(self.max_retries + 1):
            self._throttle(url)
            try:
                r = self.s.request(method, url, headers=headers, json=json_body,
                                   timeout=timeout, allow_redirects=allow_redirects)
                self._last = time.time(); self.n_requests += 1
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    self.log.error(f"[{self.source}] network fail after {attempt} retries: {e}"); return None
                delay = min(self.cap, self.base * 2**attempt) + random.random()
                self.log.warn(f"[{self.source}] net error {e}; retry in {delay:.1f}s"); time.sleep(delay); continue
            if r.status_code == 429 or r.status_code >= 500:
                self.n_429 += (r.status_code == 429)
                if attempt == self.max_retries:
                    self.log.error(f"[{self.source}] {r.status_code} exhausted retries for {url[:90]}"); return r
                ra = r.headers.get("Retry-After")
                delay = _retry_after_seconds(ra)
                if delay is None:
                    delay = min(self.cap, self.base * 2**attempt) + random.random()
                delay = min(delay, self.cap)
                self.log.warn(f"[{self.source}] {r.status_code}; backoff {delay:.1f}s (attempt {attempt+1})")
                time.sleep(delay); continue
            return r
        return None
    def get(self, url, **kw):  return self.request("GET", url, **kw)
    def post(self, url, **kw): return self.request("POST", url, **kw)

# ---------- OpenAlex helpers ----------
def oa_credit_cost(url):
    """Rough credit accounting: search= is 10, any filter/facet is 1, single-record fetch is free.
    filter=openalex_id: is ID HYDRATION (fetching known records by id) → FREE, not a 1-credit query,
    even though it's batched via the /works?filter= endpoint. Not excluding it over-reports credits
    for citation-heavy reviews (backward snowball hydrates many refs this way)."""
    if "/works/" in url.split("?")[0] and "filter=" not in url:  # single record by id/doi
        return 0
    q = urllib.parse.urlparse(url).query
    if "filter=openalex_id" in q or "filter=ids.openalex" in q:  # id hydration, free
        return 0
    if "search=" in q: return 10
    if "filter=" in q or "group_by=" in q: return 1
    return 10  # bare list default

def reconstruct_abstract(inv):
    """OpenAlex gives abstract_inverted_index {word:[positions]} → plain text."""
    if not inv: return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs: pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))

def oa_authors(work):
    return [(a.get("author") or {}).get("display_name", "") for a in (work.get("authorships") or [])]

def oa_venue(work):
    """primary_location and its .source can each be null even when the key exists."""
    loc = work.get("primary_location") or {}
    return (loc.get("source") or {}).get("display_name", "") if loc else ""

# ---------- normalization / dedup keys ----------
def norm_doi(doi):
    if not doi: return None
    d = doi.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)  # strip "doi:" / "DOI:" prefix
    return d or None

def norm_title(t):
    if not t: return ""
    t = t.lower().strip().rstrip(".")
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", t))

def first_author_surname(authors):
    if not authors: return ""
    a = authors[0] if isinstance(authors, list) else authors
    a = (a or "").strip()
    # "Surname, Given" or "Given Surname"
    if "," in a: return a.split(",")[0].strip().lower()
    return a.split(" ")[-1].strip().lower() if a else ""

# ---------- candidate record (unified shape across sources) ----------
def candidate(doi=None, title="", authors=None, year=None, venue="", abstract="",
              cited_by=None, source="", url="", extra=None, arxiv=None, pmid=None):
    return {
        "doi": norm_doi(doi), "title": title, "authors": authors or [], "year": year,
        "venue": venue, "abstract": abstract, "cited_by": cited_by,
        "arxiv": arxiv or None, "pmid": pmid or None,
        "sources": [source] if source else [], "url": url, "extra": extra or {},
    }

# ---------- small io helpers ----------
def append_jsonl(path, obj):
    with open(path, "a") as f: f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def read_jsonl(path):
    p = Path(path)
    if not p.exists(): return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2))

def now(): return dt.datetime.now().isoformat(timespec="seconds")
