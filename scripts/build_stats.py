"""Build the two README stats cards (assets/stats.svg, assets/top-langs.svg) from the GitHub API.

Runs daily from .github/workflows/stats.yml. Standard library only.
Set GITHUB_TOKEN for a higher API rate limit (the workflow does this automatically).
"""
import json
import os
import urllib.request
from html import escape
from pathlib import Path

USER = "Valorz1"
OUT = Path(__file__).resolve().parent.parent / "assets"

BG, TITLE, LABEL, VALUE, TRACK = "#181818", "#D91B24", "#BDBDBD", "#F4F4F4", "#272727"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
LANG_COLOURS = {
    "Python": "#3572A5", "Java": "#B07219", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "HTML": "#E34C26", "CSS": "#563D7C", "C++": "#F34B7D", "C": "#555555", "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89E051", "PowerShell": "#012456", "Dockerfile": "#384D54", "Kotlin": "#A97BFF", "Swift": "#F05138",
}


def get(url):
    headers = {"User-Agent": "profile-stats", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def collect():
    repos = [r for r in get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    langs = {}
    for r in repos:
        for name, size in get(r["languages_url"]).items():
            langs[name] = langs.get(name, 0) + size
    return {
        "repos": len(repos),
        "stars": sum(r["stargazers_count"] for r in repos),
        "commits": get(f"https://api.github.com/search/commits?q=author:{USER}")["total_count"],
        "prs": get(f"https://api.github.com/search/issues?q=author:{USER}+type:pr")["total_count"],
        "langs": langs,
    }


def card(width, height, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(title)}">\n'
        f'  <rect width="{width}" height="{height}" rx="10" fill="{BG}"/>\n'
        f'  <text x="24" y="38" font-family="{FONT}" font-size="17" font-weight="600" fill="{TITLE}">{escape(title)}</text>\n'
        f"{body}</svg>\n"
    )


def stats_svg(s):
    rows = [("Public repositories", s["repos"]), ("Commits (public)", s["commits"]),
            ("Pull requests", s["prs"]), ("Stars earned", s["stars"])]
    body = ""
    for i, (label, value) in enumerate(rows):
        y = 74 + i * 26
        body += (
            f'  <rect x="24" y="{y - 9}" width="8" height="8" rx="2" fill="{TITLE}"/>\n'
            f'  <text x="42" y="{y}" font-family="{FONT}" font-size="14" fill="{LABEL}">{label}</text>\n'
            f'  <text x="356" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="600" fill="{VALUE}">{value:,}</text>\n'
        )
    return card(380, 180, f"{USER} on GitHub", body)


def langs_svg(langs, top=6):
    total = sum(langs.values()) or 1
    items = sorted(langs.items(), key=lambda kv: -kv[1])[:top]
    shown = sum(v for _, v in items) or 1
    body, x = "", 24.0
    body += f'  <clipPath id="bar"><rect x="24" y="56" width="332" height="10" rx="5"/></clipPath>\n'
    body += f'  <rect x="24" y="56" width="332" height="10" rx="5" fill="{TRACK}"/>\n  <g clip-path="url(#bar)">\n'
    for name, size in items:
        w = 332 * size / shown
        body += f'    <rect x="{x:.2f}" y="56" width="{w:.2f}" height="10" fill="{LANG_COLOURS.get(name, "#8A8A8A")}"/>\n'
        x += w
    body += "  </g>\n"
    for i, (name, size) in enumerate(items):
        col, row = i % 2, i // 2
        cx, cy = 24 + col * 170, 98 + row * 26
        body += (
            f'  <circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{LANG_COLOURS.get(name, "#8A8A8A")}"/>\n'
            f'  <text x="{cx + 16}" y="{cy}" font-family="{FONT}" font-size="14" fill="{LABEL}">{escape(name)} '
            f'<tspan fill="{VALUE}" font-weight="600">{100 * size / total:.1f}%</tspan></text>\n'
        )
    return card(380, 180, "Most used languages", body)


if __name__ == "__main__":
    data = collect()
    OUT.mkdir(exist_ok=True)
    (OUT / "stats.svg").write_text(stats_svg(data), encoding="utf-8")
    (OUT / "top-langs.svg").write_text(langs_svg(data["langs"]), encoding="utf-8")
    print(f"repos={data['repos']} commits={data['commits']} prs={data['prs']} stars={data['stars']} languages={len(data['langs'])}")
