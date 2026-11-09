
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

# Website configuration
BASE_URL = "https://www.akgec.ac.in/"
OUTPUT_FILE = Path("data/navigation_urls.json")

# Exclude non-content links
SKIP_PATHS = (
    "/cdn-cgi/",
    "/wp-admin/",
    "/wp-login",
)

SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png",
    ".webp", ".gif", ".zip", ".mp4"
)


def main():
    response = requests.get(BASE_URL, timeout=20)# website se html lena
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    selected = []
    skipped = []
    seen = set()

    # Discover navigation links
    for link in soup.select("header a[href], nav a[href]"):
        title = link.get_text(" ", strip=True)
        raw_url = link.get("href", "").strip()

        url = urljoin(BASE_URL, raw_url)
        url, _ = urldefrag(url)

        parsed = urlparse(url)  #URL analyze karna
        path = parsed.path.lower()

        if not title or not raw_url:
            continue

        if parsed.netloc.lower() not in (
            "www.akgec.ac.in",
            "akgec.ac.in"
        ):
            continue

        if (
            raw_url.startswith("#")
            or parsed.query
            or path.endswith(SKIP_EXTENSIONS)
            or any(path.startswith(p) for p in SKIP_PATHS)
        ):
            skipped.append(title)
            continue

        normalized_path = parsed.path.rstrip("/") or "/"
        normalized_url = (
            "https://www.akgec.ac.in" + normalized_path
        )

        if normalized_url in seen:
            continue

        seen.add(normalized_url)

        selected.append({
            "title": title,
            "url": normalized_url,
            "status": "pending_review"
        })

    # Save discovered HTML URLs
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            selected,
            file,
            indent=2,
            ensure_ascii=False
        )

    print("\n===== NAVIGATION REPORT =====")
    print("Selected HTML URLs:", len(selected))
    print("Skipped links:", len(skipped))
    print("Saved to:", OUTPUT_FILE)

    print("\n===== SELECTED PAGES =====")

    for index, item in enumerate(selected, start=1):
        print(f"{index}. {item['title']}")


if __name__ == "__main__":
    main()
