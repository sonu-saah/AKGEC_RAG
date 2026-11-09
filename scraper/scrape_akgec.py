
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

INPUT = Path("data/selected_urls.json")
OUTPUT = Path("data/akgec_structured.json")
ERRORS = Path("data/scraping_errors.json")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (AKGEC academic information research)"
})

with INPUT.open(encoding="utf-8") as f:
    pages = json.load(f)

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_page(page):
    response = session.get(page["url"], timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup.select(
        "script, style, noscript, svg, img, "
        "header, footer, nav, form, iframe, "
        ".navbar, .menu, .breadcrumb, "
        ".sidebar, .site-header, .site-footer"
    ):
        element.decompose()

    main = (
        soup.select_one("main")
        or soup.select_one("article")
        or soup.select_one(".entry-content")
        or soup.select_one(".page-content")
        or soup.body
    )

    if main is None:
        return []

    blocks = []
    seen = set()

    for element in main.find_all(
        ["h1", "h2", "h3", "h4", "h5", "p", "li", "table"]
    ):
        # Avoid nested duplicate text
        if element.find_parent(["li", "table"]):
            continue

        if element.name == "table":
            rows = []
            for tr in element.find_all("tr"):
                cells = [
                    clean(cell.get_text(" ", strip=True))
                    for cell in tr.find_all(["th", "td"])
                ]
                if any(cells):
                    rows.append(cells)

            if rows:
                key = json.dumps(rows, ensure_ascii=False)
                if key not in seen:
                    seen.add(key)
                    blocks.append({
                        "type": "table",
                        "rows": rows
                    })
            continue

        text = clean(element.get_text(" ", strip=True))

        if len(text) < 3:
            continue

        key = text.casefold()

        if key in seen:
            continue

        seen.add(key)

        if element.name.startswith("h"):
            block_type = "heading"
            level = int(element.name[1])
        elif element.name == "li":
            block_type = "list_item"
            level = None
        else:
            block_type = "paragraph"
            level = None

        blocks.append({
            "type": block_type,
            "level": level,
            "text": text
        })

    return blocks

def library_filter(blocks):
    allowed = (
        "about akgec central library",
        "about the library",
        "library team",
        "contact us"
    )

    result = []
    active = False

    for block in blocks:
        if block["type"] == "heading":
            title = block["text"].lower()
            active = any(x in title for x in allowed)

        if active:
            result.append(block)

    return result

results = []
errors = []

for index, page in enumerate(pages, 1):
    print(f"[{index}/{len(pages)}] {page['title']}", flush=True)

    try:
        blocks = extract_page(page)

        if page["title"] == "Library":
            blocks = library_filter(blocks)

        if not blocks:
            errors.append({
                "title": page["title"],
                "url": page["url"],
                "error": "No relevant content extracted"
            })
        else:
            results.append({
                "title": page["title"],
                "source_url": page["url"],
                "status": "needs_content_review",
                "blocks": blocks
            })

    except Exception as error:
        errors.append({
            "title": page["title"],
            "url": page["url"],
            "error": str(error)
        })

    time.sleep(0.5)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

with ERRORS.open("w", encoding="utf-8") as f:
    json.dump(errors, f, indent=2, ensure_ascii=False)

print("\n===== SCRAPING REPORT =====")
print("Selected URLs:", len(pages))
print("Pages with extracted content:", len(results))
print("Pages requiring review:", len(errors))
print("Structured data:", OUTPUT)
print("Errors:", ERRORS)

