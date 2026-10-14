# Discover relevant AKGEC navigation URLs

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.akgec.ac.in/"
OUTPUT_FILE = Path("data/fresh/navigation_urls.json")

HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}

SECTIONS = {
    "ABOUT",
    "DEPARTMENTS",
    "ACADEMICS",
    "ADMISSIONS",
    "R&D",
    "CENTRES OF EXCELLENCE",
    "COLLEGE PUBLICATIONS",
    "LIFE@AKGEC",
    "ACHIEVEMENTS",
    "PLACEMENTS",
    "VE CELL",
    "IQAC",
    "CAREER",
}

SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png",
    ".webp", ".gif", ".zip", ".doc", ".docx",
    ".xls", ".xlsx", ".mp4"
)

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in"
}


# Normalize website URLs
def normalize_url(href):
    absolute_url = urljoin(BASE_URL, href)
    absolute_url, _ = urldefrag(absolute_url)

    parsed = urlparse(absolute_url)

    if parsed.scheme != "https":
        return None

    if parsed.netloc.lower() not in ALLOWED_DOMAINS:
        return None

    if parsed.path.lower().endswith(SKIP_EXTENSIONS):
        return None

    if parsed.query:
        return None

    path = parsed.path.rstrip("/") or "/"

    return f"https://www.akgec.ac.in{path}"


# Discover navigation pages
def main():
    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select("header a[href], nav a[href]")

    current_section = None
    discovered = []
    seen = set()

    for link in links:
        title = link.get_text(" ", strip=True)
        href = link.get("href", "").strip()

        if not title or not href:
            continue

        upper_title = title.upper()

        if upper_title in SECTIONS:
            current_section = upper_title

        # IQAC and CAREER are standalone sections
        if upper_title in {"IQAC", "CAREER"}:
            section = upper_title
        else:
            section = current_section

        if section is None:
            continue

        url = normalize_url(href)

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        discovered.append({
            "section": section,
            "title": title,
            "url": url
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {
                "total_urls": len(discovered),
                "pages": discovered
            },
            file,
            ensure_ascii=False,
            indent=2
        )

    print("Total unique webpage URLs:", len(discovered))

    counts = {}

    for item in discovered:
        section = item["section"]
        counts[section] = counts.get(section, 0) + 1

    for section, count in counts.items():
        print(f"{section}: {count}")

    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()