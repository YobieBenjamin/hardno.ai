#!/usr/bin/env python3
"""Build and self-check the hardno.ai website (the Safety Governor's public home page).

One command:
    python3 build.py --url https://hardno.ai/

What it does, in order:
  1. build():  copies src/ to dist/ and fills in the two blanks every page has: the public address
               ({{SITE_URL}}) and today's date ({{TODAY}}). dist/ is what actually gets published.
  2. check():  inspects dist/ the way a search engine, an AI crawler, a browser and a hacker would,
               and refuses to pass if anything is wrong.

Think of it as the preflight checklist on a plane: the plane does not leave the gate until every box
is ticked. The GitHub publishing workflow (.github/workflows/pages.yml) runs this exact script, so a
page that fails any check here can never reach the live site.

The checks fall into five groups:
  - findability:  title and description lengths, one headline per page, canonical address, social
                  preview tags, structured data for search engines, key phrases in the visible text
  - crawlers:     robots.txt welcomes every search engine and AI crawler and points at the sitemap
  - safety:       each page carries a locked Content-Security-Policy, loads script only from its own
                  assets/ folder, and has no inline code a browser could be tricked into running
  - house style:  no em or en dashes, no unfilled {{placeholders}}
  - documentation: every code file explains itself (the project's standing rule), checked so the rule
                  cannot quietly lapse

It uses only Python's standard library, so it runs anywhere Python 3 does, with nothing to install.
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

# Folders, all relative to this script so it works from any current directory.
HERE = Path(__file__).resolve().parent
SRC = HERE / "src"      # what we edit
DIST = HERE / "dist"    # what we publish (rebuilt from scratch every run; never edit it by hand)

# Phrases we want search engines and AI answer engines to tie to this project.
# The front page must say each one in its visible text, not just in a hidden meta tag, because
# search engines discount keywords that only appear where readers can't see them.
# ("abliterat" is a stem: it matches "abliterated" and "abliteration".)
MUST_MENTION = [
    "AI safety", "AI kill switch", "AI safety chip", "governor chip", "compute governance",
    "AI control", "human oversight", "rogue AI", "NVIDIA", "Menger", "can't be the referee",
    "abliterat", "open weights", "model weights",
]

# File types that hold text (and so can carry placeholders, dashes and comments). Images are skipped.
TEXT_FILES = {".html", ".txt", ".xml", ".svg", ".css", ".js"}

# Every page on the site, and what each must contain:
#   path:    the page's address relative to the site root ("" is the front page)
#   types:   the structured-data (JSON-LD) types search engines must find on it
#   mention: phrases its visible text must contain (None means use MUST_MENTION)
# The front page carries the site-wide structured data (who runs the site, the research project, the FAQ).
PAGES = {
    "index.html": {"path": "", "types": ("WebSite", "Person", "ResearchProject", "FAQPage"), "mention": None},
    "use-cases.html": {"path": "use-cases.html", "types": ("Article", "BreadcrumbList"),
                       "mention": ["AI safety", "banking", "trading", "insurance", "healthcare", "power grid", "cloud", "governed", "no ticket, no move"]},
    "methodology.html": {"path": "methodology.html", "types": ("Article", "BreadcrumbList"),
                         "mention": ["tamper theorem", "Property 1", "Property 2", "fleet", "ticket", "Experiment A", "Experiment B", "assumption"]},
    "case-against.html": {"path": "case-against.html", "types": ("Article", "BreadcrumbList"),
                          "mention": ["identical silicon", "shared cap", "endpoint", "replica", "the answer", "do not bite"]},
}

# Documentation rule: each code file must open with a comment that explains what it is.
# Key: file inside src/; value: the text that must start the file's explanatory comment.
MUST_EXPLAIN = {
    "index.html": "<!--",
    "use-cases.html": "<!--",
    "methodology.html": "<!--",
    "case-against.html": "<!--",
    "assets/site.css": "/*",
    "assets/site.js": "/*",
}


class PageScan(HTMLParser):
    """Walks the HTML once and collects what the checks need, like a building inspector's clipboard.

    It records the page title, every <meta> tag, every <link> tag, how many <h1> headlines there are,
    images missing alt text (which hurts both blind visitors and image search), the structured-data
    blocks, and all visible text (so we can check the key phrases are really on the page).
    """

    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False       # are we inside <title> right now?
        self.meta = {}               # meta name or property -> content
        self.links = []              # each <link> tag's attributes
        self.h1 = 0
        self.imgs_without_alt = 0
        self.jsonld = []             # the raw text of each structured-data block
        self._in_jsonld = False      # are we inside a <script type="application/ld+json">?
        self._buf = []
        self.text = []               # visible text, in order

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            # Search tags use name= (description, robots); social preview tags use property= (og:title).
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and not a.get("alt"):
            self.imgs_without_alt += 1
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            self.jsonld.append("".join(self._buf))

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_jsonld:
            self._buf.append(data)   # structured data is for machines; keep it out of the visible text
        else:
            self.text.append(data)


def build(url: str) -> None:
    """Copy src/ to a fresh dist/ and fill in the address and date blanks."""
    if not url.endswith("/"):
        url += "/"
    today = datetime.date.today().isoformat()
    if DIST.exists():
        shutil.rmtree(DIST)          # start clean, so a file deleted from src/ can't linger on the live site
    shutil.copytree(SRC, DIST)
    for f in DIST.rglob("*"):
        if f.is_file() and f.suffix in TEXT_FILES:
            s = f.read_text(encoding="utf-8")
            f.write_text(s.replace("{{SITE_URL}}", url).replace("{{TODAY}}", today), encoding="utf-8")
    # GitHub Pages would otherwise run the files through Jekyll (a site generator we don't use);
    # this empty file tells it to serve them exactly as built.
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built dist/ for {url}")


def check(url: str) -> int:
    """Inspect dist/. Print every problem found; return 0 if there are none, 1 otherwise."""
    if not url.endswith("/"):
        url += "/"
    problems = []

    def need(ok, msg):
        # Collect problems instead of stopping at the first one, so one run shows everything to fix.
        if not ok:
            problems.append(msg)

    types = set()
    for page, spec in PAGES.items():
        html = (DIST / page).read_text(encoding="utf-8")

        # ---- Safety: what a visitor's browser is allowed to do with this page.
        # The Content-Security-Policy is the page's own bouncer: it tells the browser to run script only
        # from this site and load nothing else except the fonts. Even if someone slipped a script into
        # the page, the browser would refuse to run it.
        need("Content-Security-Policy" in html and "script-src 'self';" in html and "default-src 'none'" in html,
             f"{page}: missing the locked Content-Security-Policy")
        # The only script tags allowed: structured data (which browsers never run) and our own file in assets/.
        for tag in re.findall(r"<script\b[^>]*>", html):
            need('type="application/ld+json"' in tag or re.fullmatch(r'<script src="assets/[\w.-]+\.js">', tag),
                 f"{page}: script tag not allowed: {tag}")
        # No onclick= style handlers and no javascript: links; both are ways to run code from inside the HTML.
        need(not re.search(r"\son[a-z]+\s*=", html, re.I) and "javascript:" not in html.lower(),
             f"{page}: inline event handler or javascript: link")

        # ---- Findability: what search engines and AI crawlers read.
        p = PageScan()
        p.feed(html)
        visible = re.sub(r"\s+", " ", "".join(p.text))   # collapse line breaks so phrases split across lines still match
        here = url + spec["path"]                          # this page's full public address
        # Google shows about 60 characters of a title and about 155 of a description; outside these ranges it cuts or rewrites them.
        need(10 <= len(p.title) <= 65, f"{page}: title should be 10 to 65 characters, is {len(p.title)}: {p.title!r}")
        d = p.meta.get("description", "")
        need(120 <= len(d) <= 165, f"{page}: meta description should be 120 to 165 characters, is {len(d)}")
        need(p.h1 == 1, f"{page}: needs exactly one h1, has {p.h1}")
        need(p.imgs_without_alt == 0, f"{page}: {p.imgs_without_alt} image(s) missing alt text")
        # The canonical link tells search engines "this is the one true address of this page".
        canon = [l.get("href") for l in p.links if l.get("rel") == "canonical"]
        need(canon == [here], f"{page}: canonical should be {here}, is {canon}")
        # Social preview tags: what LinkedIn, X, Slack and iMessage show when someone shares the link.
        for key in ("og:title", "og:description", "og:url", "og:image", "twitter:card"):
            need(bool(p.meta.get(key)), f"{page}: missing {key}")
        need(p.meta.get("og:url") == here, f"{page}: og:url does not match the page address")
        need("noindex" not in p.meta.get("robots", ""), f"{page}: robots meta says noindex")
        # Structured data (JSON-LD) is a machine-readable summary search engines use for rich results.
        need(len(p.jsonld) >= 1, f"{page}: no JSON-LD structured data")
        ptypes = set()
        for block in p.jsonld:
            try:
                data = json.loads(block)
                for node in data.get("@graph", [data]):   # a block is either one item or a @graph list of items
                    ptypes.add(node.get("@type"))
            except json.JSONDecodeError as e:
                problems.append(f"{page}: JSON-LD does not parse: {e}")
        for t in spec["types"]:
            need(t in ptypes, f"{page}: JSON-LD missing {t}")
        types |= ptypes
        for phrase in (spec["mention"] or MUST_MENTION):
            need(phrase.lower() in visible.lower(), f"{page}: visible page text never says {phrase!r}")
        # Every link to another page of this site must point at a file that exists (no dead links).
        for target in re.findall(r'href="([a-z0-9-]+\.html)(?:#[^"]*)?"', html):
            need((DIST / target).exists(), f"{page}: links to {target}, which does not exist")
        need(f"<loc>{here}</loc>" in (DIST / "sitemap.xml").read_text(encoding="utf-8"), f"sitemap is missing {here}")

    # ---- Crawlers: robots.txt is the site's welcome sign for bots.
    robots = (DIST / "robots.txt").read_text(encoding="utf-8")
    need(f"Sitemap: {url}sitemap.xml" in robots, "robots.txt does not point at the sitemap")
    need(not re.search(r"^Disallow:\s*/\s*$", robots, re.M), "robots.txt blocks the whole site")
    # Name the major AI crawlers explicitly, so no "block unknown bots" default shuts them out.
    for bot in ("GPTBot", "ClaudeBot", "Google-Extended", "PerplexityBot", "CCBot"):
        need(f"User-agent: {bot}" in robots, f"robots.txt does not name {bot}")
    need((DIST / "llms.txt").exists(), "llms.txt missing")          # plain-text summary for AI answer engines
    need((DIST / "og.png").exists(), "og.png social preview image missing")

    # ---- House style: no em or en dashes anywhere, and no unfilled placeholders.
    # (The dashes are written as \u2014 and \u2013 escape codes so this file passes its own rule.)
    for f in DIST.rglob("*"):
        if f.is_file() and f.suffix in TEXT_FILES:
            s = f.read_text(encoding="utf-8")
            need("\u2014" not in s and "\u2013" not in s, f"{f.name} contains an em or en dash")
            need("{{" not in s, f"{f.name} has an unfilled {{{{placeholder}}}}")

    # ---- Documentation: every code file explains itself near the top (standing project rule).
    # For HTML the explanation comes right after the <!doctype html> line; CSS and JS open with it.
    for name, opener in MUST_EXPLAIN.items():
        s = (DIST / name).read_text(encoding="utf-8")
        head = re.sub(r"^<!doctype html>\s*", "", s, flags=re.I).lstrip()
        need(head.startswith(opener), f"{name}: must open with an explanatory comment ({opener} ...)")
        # A file this size with almost no comments has not really been documented; ask for at least 8.
        count = s.count("<!--") if opener == "<!--" else s.count("/*")
        need(count >= 8, f"{name}: only {count} comments; explain each section so another developer can follow it")

    if problems:
        print("FAILED:")
        for m in problems:
            print("  - " + m)
        return 1
    print(f"all checks passed ({len(PAGES)} pages, JSON-LD types: {sorted(t for t in types if t)})")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="public address the site will live at, e.g. https://hardno.ai/")
    args = ap.parse_args()
    build(args.url)
    sys.exit(check(args.url))   # a non-zero exit stops the GitHub workflow before anything is published
