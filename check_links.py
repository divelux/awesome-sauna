#!/usr/bin/env python3
"""Check every link in README.md. Standard library only.

    python3 check_links.py

Prints one line per link and exits 1 if any link fails. Some sites refuse
scripts (bot checks) and answer 403 even though the page is fine in a browser;
those are listed in BROWSER_ONLY and reported as "check by hand".
"""
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

README = Path(__file__).with_name("README.md")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
# Hosts that block scripted requests. Checked by hand in a browser or through a search engine.
BROWSER_ONLY = ("saunainternational.net", "doi.org/10.1001/", "doi.org/10.1016/", "www.heart.org", "support.harvia.com")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en", "Accept": "text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url
    except Exception as e:  # DNS, TLS, timeout
        return 0, f"{url} ({e.__class__.__name__})"


def main():
    text = README.read_text(encoding="utf-8")
    links = []
    for m in re.finditer(r"\]\((https?://[^)\s]+(?:\([^)\s]*\)[^)\s]*)*)\)", text):
        if m.group(1) not in links:
            links.append(m.group(1))
    bad = 0
    by_hand = 0
    for url in links:
        status, final = fetch(url)
        if 200 <= status < 300:
            note = "ok" if final.rstrip("/") == url.rstrip("/") else f"ok -> {final}"
        elif any(h in url for h in BROWSER_ONLY):
            note = "check by hand (blocks scripts)"
            by_hand += 1
        else:
            note = "FAILED"
            bad += 1
        print(f"{status:3d} {url}  {note}")
    entries = len(re.findall(r"^- \[", text, re.M))
    print(f"\n{len(links)} links, {entries} list entries, {bad} failed, {by_hand} to check by hand")
    # format: every entry is "- [Name](url) - Sentence." (an extra "([source](url))" is allowed)
    for line in text.splitlines():
        if line.startswith("- [") and "](#" not in line:
            if not re.match(r"^- \[[^\]]+\]\(https?://\S+\) - [A-Z].*[.)]$", line):
                print("format:", line[:90])
                bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
