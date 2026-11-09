
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

# Load approved URLs
with open("data/selected_urls.json", encoding="utf-8") as file:
    pages = json.load(file)

# Inspect only pages relevant to missing topics
keywords = (
    "library", "department", "courses offered",
    "fee structure", "scholarship"
)

targets = [
    page for page in pages
    if any(word in page["title"].lower() for word in keywords)
]

# Also inspect main website for missing admission links
targets.append({
    "title": "AKGEC Home",
    "url": "https://www.akgec.ac.in/"
})

link_keywords = (
    "library", "syllabus", "curriculum",
    "admission", "enquiry", "inquiry",
    "uptac", "reporting", "counselling",
    "faculty", "laboratory", "lab",
    "about us", "contact us", "team"
)

results = []
seen = set()
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

for page in targets:
    print("Checking:", page["title"])

    try:
        response = session.get(page["url"], timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.select("a[href]"):
            title = link.get_text(" ", strip=True)
            raw_url = link.get("href", "").strip()
            url, _ = urldefrag(urljoin(page["url"], raw_url))
            parsed = urlparse(url)

            if parsed.hostname not in ("akgec.ac.in", "www.akgec.ac.in"):
                continue

            if parsed.path.lower().endswith(
                (".jpg", ".png", ".jpeg", ".webp", ".zip", ".mp4")
            ):
                continue

            searchable = (title + " " + parsed.path).lower()

            if not any(word in searchable for word in link_keywords):
                continue

            if url in seen:
                continue

            seen.add(url)
            results.append({
                "title": re.sub(r"\s+", " ", title),
                "url": url,
                "found_on": page["title"],
                "status": "pending_review"
            })

    except requests.RequestException as error:
        print("Failed:", error)

# Save link candidates for review
output = Path("data/internal_link_candidates.json")
output.parent.mkdir(parents=True, exist_ok=True)

with open(output, "w", encoding="utf-8") as file:
    json.dump(results, file, indent=2, ensure_ascii=False)

print("\n===== DISCOVERY REPORT =====")
print("Pages checked:", len(targets))
print("Candidate links:", len(results))
print("Saved to:", output)

for index, item in enumerate(results, 1):
    print(f"{index}. {item['title']} -> {item['url']}")
