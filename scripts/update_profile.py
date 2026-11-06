#!/usr/bin/env python3
"""Refresh a restrained monochrome dashboard using public GitHub repository metadata."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

DARK, IVORY = "#111111", "#F5F3EE"
OUTPUT = Path("assets/profile-dashboard.svg")


def fetch_repos(user: str) -> list:
    token = os.environ.get("GH_TOKEN", "")
    repos = []
    for page in range(1, 11):
        url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}&type=owner"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "monochrome-profile"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        with urlopen(Request(url, headers=headers), timeout=25) as response:
            batch = json.load(response)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
    raise RuntimeError("Repository pagination exceeded 1,000 entries")


def dashboard(repos: list, user: str, stamp: str) -> str:
    public = [r for r in repos if not r.get("private") and not r.get("archived") and not r.get("fork")]
    stars = sum(int(r.get("stargazers_count") or 0) for r in public)
    langs = Counter(r["language"] for r in public if r.get("language"))
    newest = sorted(public, key=lambda r: r.get("pushed_at") or "", reverse=True)
    lang = "  /  ".join(escape(name.upper()) for name, _ in langs.most_common(4)) or "NO LANGUAGE DATA"
    latest = escape((newest[0]["name"] if newest else "NO PUBLIC REPOS")[:42])
    metrics = [("REPOSITORIES", str(len(public))), ("STARS", str(stars)), ("LANGUAGES", str(len(langs)))]
    segments = []
    for i, (label, value) in enumerate(metrics):
        x = 55 + i * 307
        segments += [
            f'<rect x="{x}" y="106" width="276" height="142" fill="{IVORY}"/>',
            f'<text x="{x+18}" y="142" fill="{DARK}" font-size="15" font-weight="700" letter-spacing="1.5">{label}</text>',
            f'<text x="{x+18}" y="220" fill="{DARK}" font-size="67" font-weight="700">{escape(value)}</text>',
        ]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="404" viewBox="0 0 1000 404" role="img" aria-labelledby="title desc">
<title id="title">Public GitHub activity for {escape(user)}</title>
<desc id="desc">Updated {stamp}; public non-fork repository count, stars, programming languages, and latest pushed repository.</desc>
<rect width="1000" height="404" fill="{DARK}"/>
<text x="55" y="63" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="25" font-weight="700" letter-spacing="3">GITHUB / OVERVIEW</text>
<text x="945" y="61" text-anchor="end" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="14">{stamp} UTC</text>
<path d="M55 81 H945" stroke="{IVORY}" stroke-width="1.5"/>
<g font-family="Arial,Helvetica,sans-serif">{''.join(segments)}</g>
<text x="55" y="294" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="14" font-weight="700" letter-spacing="2">MOST USED REPO LANGUAGES</text>
<text x="55" y="323" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="20">{lang}</text>
<path d="M55 345 H945" stroke="{IVORY}" stroke-width="1" opacity=".7"/>
<text x="55" y="377" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="14" font-weight="700">LATEST ACTIVE REPO</text>
<text x="945" y="377" text-anchor="end" fill="{IVORY}" font-family="Arial,Helvetica,sans-serif" font-size="17">{latest}</text>
</svg>
'''


def recolor_cards() -> None:
    """Make two existing generated cards match the two-color palette."""
    folder = Path("profile-summary-card-output/github_dark")
    for filename in ("0-profile-details.svg", "3-stats.svg"):
        path = folder / filename
        if not path.exists():
            raise FileNotFoundError(path)
        source = path.read_text(encoding="utf-8")
        import re
        source = re.sub(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", lambda m: DARK if m.group(0).lower() in {"#0d1117", "#2e343b", "#000000"} else IVORY, source)
        # A uniform dark canvas, warm-white foreground and lines.
        source = source.replace('fill="#262626"', f'fill="{DARK}"')
        path.write_text(source, encoding="utf-8")


def main() -> None:
    user = os.environ.get("PROFILE_USER", "YEYE2e")
    try:
        repos = fetch_repos(user)
    except (URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(f"Cannot fetch repository data; keeping last good dashboard: {exc}") from exc
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(dashboard(repos, user, stamp), encoding="utf-8")
    recolor_cards()
    print(f"Updated {OUTPUT} and two monochrome summary cards from {len(repos)} GitHub repositories")


if __name__ == "__main__":
    main()
