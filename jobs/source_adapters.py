"""First-party/public job-feed adapters.

Supported providers:
- Greenhouse public Job Board API (board token)
- Lever public Postings API (site/company slug)
- Generic JSON, RSS/Atom and CSV URLs

This module never logs in, bypasses CAPTCHAs, or accesses restricted pages.
"""
import csv
import io
import json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests

from .collector import deduplicate

TIMEOUT = 20
UA = "AI-Job-Search-Assistant/7.4"


def _check_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Feed URL must be an http(s) URL.")


def _get(url):
    _check_url(url)
    response = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": UA, "Accept": "application/json, application/xml, text/xml, text/csv, */*"})
    response.raise_for_status()
    return response


def _json_jobs(payload):
    if isinstance(payload, dict):
        for key in ("jobs", "results", "items", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return [payload]
    return payload if isinstance(payload, list) else []


def _greenhouse(source):
    token = str(source.get("board_token") or "").strip()
    if not token:
        raise ValueError("Greenhouse board token is required.")
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    payload = _get(url).json()
    rows = []
    for item in payload.get("jobs", []):
        loc = (item.get("location") or {}).get("name", "")
        rows.append({
            "title": item.get("title", ""),
            "company": source.get("company") or source.get("name", "Greenhouse"),
            "location": loc,
            "url": item.get("absolute_url", ""),
            "description": item.get("content", ""),
            "source": source.get("name", "Greenhouse"),
        })
    return url, rows


def _lever(source):
    site = str(source.get("site") or "").strip()
    if not site:
        raise ValueError("Lever site/company slug is required.")
    url = f"https://api.lever.co/v0/postings/{site}?mode=json"
    payload = _get(url).json()
    rows = []
    for item in payload if isinstance(payload, list) else []:
        categories = item.get("categories") or {}
        loc = categories.get("location") or ", ".join(categories.get("allLocations") or [])
        description = item.get("descriptionPlain") or item.get("description") or item.get("lists") or ""
        if isinstance(description, list):
            description = " ".join(str(x) for x in description)
        rows.append({
            "title": item.get("text", ""),
            "company": source.get("company") or source.get("name", "Lever"),
            "location": loc,
            "url": item.get("hostedUrl") or item.get("applyUrl") or "",
            "description": description,
            "source": source.get("name", "Lever"),
        })
    return url, rows


def _rss_jobs(text):
    root = ET.fromstring(text)
    rows = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item") or root.findall(".//atom:entry", ns)
    for item in items:
        def val(*paths):
            for path in paths:
                node = item.find(path, ns) if ":" in path else item.find(path)
                if node is not None and (node.text or "").strip():
                    return node.text.strip()
            return ""
        link_node = item.find("atom:link", ns)
        link = (link_node.attrib.get("href", "") if link_node is not None else "") or val("link")
        rows.append({
            "title": val("title", "atom:title"),
            "company": val("company", "author", "atom:author/atom:name"),
            "location": val("location"),
            "url": link,
            "description": val("description", "summary", "atom:summary", "atom:content"),
        })
    return rows


def _generic(source):
    url = str(source.get("url", "")).strip()
    fmt = str(source.get("format") or "auto").lower()
    response = _get(url)
    content_type = response.headers.get("content-type", "").lower()
    text = response.text
    if fmt == "json" or (fmt == "auto" and "json" in content_type):
        rows = _json_jobs(response.json())
    elif fmt == "csv" or (fmt == "auto" and ("csv" in content_type or url.lower().endswith(".csv"))):
        rows = list(csv.DictReader(io.StringIO(text)))
    else:
        rows = _rss_jobs(text)
    return url, rows


def fetch_source(source):
    provider = str(source.get("provider") or "generic").lower()
    if provider == "greenhouse":
        url, rows = _greenhouse(source)
    elif provider == "lever":
        url, rows = _lever(source)
    else:
        url, rows = _generic(source)

    normalized = []
    for row in rows:
        if isinstance(row, dict):
            row = dict(row)
            row["source"] = source.get("name") or row.get("source") or "Public Feed"
            normalized.append(row)
    jobs = deduplicate(normalized)
    return {"source": source.get("name", "Public Feed"), "provider": provider, "url": url, "count": len(jobs), "jobs": jobs}


def fetch_sources(sources):
    results = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        try:
            results.append({"ok": True, **fetch_source(source)})
        except Exception as exc:
            results.append({"ok": False, "source": source.get("name", "Unnamed"), "provider": source.get("provider", "generic"), "url": source.get("url", ""), "error": str(exc), "count": 0, "jobs": []})
    return results
