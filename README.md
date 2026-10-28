# hardno.ai: the Safety Governor website

The public, crawlable home page for the Safety Governor: an AI safety chip, because there is no AI kill switch.

## One command

    python3 build.py --url https://hardno.ai/

That builds `dist/` and runs every findability check: title and description length, one headline,
canonical address, social preview tags, structured data (WebSite, Person, ResearchProject, FAQPage),
the key phrases actually on the page, robots.txt welcoming every search engine and AI crawler,
sitemap, llms.txt, and the house style (no em or en dashes, no unfilled placeholders).
If anything fails, it says what and refuses to pass.

## Publishing

Put this folder in a GitHub repository. `.github/workflows/pages.yml` builds, checks and publishes
to GitHub Pages on every change to main. One-time setup by a person: in the repository's settings,
turn on Pages with "GitHub Actions" as the source, and set the variable `SITE_URL` to `https://hardno.ai/` and point the hardno.ai domain at GitHub Pages.

## What is in src/

- `index.html`: the whole site, readable with no JavaScript, so every crawler sees every word
- `robots.txt`: allows Google, Bing, GPTBot, ClaudeBot, Google-Extended, PerplexityBot, CCBot and the rest
- `sitemap.xml`: tells search engines what to index
- `llms.txt`: a plain-text summary written for AI systems and answer engines
- `og.png`: the preview card shown when the link is shared on LinkedIn, X, Slack or iMessage
- `favicon.svg`: the tab icon
- `assets/site.css`, `assets/site.js`: the look, and the one small script (the rotating mottos)

## Documented code (a standing project rule)

Every code file explains itself in plain English, in comments, so another developer or an auditor can pick it up
without guessing: the HTML pages, the stylesheet, the script, `build.py`, the logo script and the workflows.
`build.py` enforces it for the site: a page, stylesheet or script without its explanatory opening comment and
section comments fails the build, and a failed build never publishes.

## Locked down

- Each page carries a Content-Security-Policy: the browser runs script only from this site's own files and loads
  nothing else but the fonts. `build.py` refuses a page without it, or with any outside script or inline code.
- `.github/workflows/pages.yml` uses only GitHub's own actions, pinned to exact commits, with minimal permissions.
- `.github/workflows/watch.yml` is the tamper alarm: every 6 hours it checks the live site byte for byte against
  main and fails (emailing the owner) if anything differs.
- The repository itself is locked by `harden_site.sh` (in the launchers): only the owner has access, main changes
  only by pull request, nothing can be force-pushed or deleted, and only main can publish.

## Brand

`src/assets/brand/` holds the hardno.ai logo: the lockup and the mark, for dark and light backgrounds, as SVG (vector, any size) and PNG. The mark is a chip seen from above whose die is a stop-sign octagon. The wordmark is IBM Plex Sans Condensed Bold, converted to outlines, with "no" in signal red #FF5B35. `brand/make_logo.py` redraws every logo file from the IBM Plex font (install it with `npm install @fontsource/ibm-plex-sans-condensed`).
