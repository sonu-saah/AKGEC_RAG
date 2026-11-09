
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

# Test three different website page types
TEST_PAGES = [
    {
        "title": "Vision And Mission",
        "url": "https://www.akgec.ac.in/vision-and-mission"
    },
    {
        "title": "Computer Science and Engineering",
        "url": "https://www.akgec.ac.in/departments/computer-science-and-engineering"
    },
    {
        "title": "Fee Structure for New Students",
        "url": "https://www.akgec.ac.in/fee-structure-for-new-students2026-27"
    }
]

OUTPUT = Path("data/extraction_test.json")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def extract_content(url):
    response = session.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    container = (
        soup.select_one(".entry-content")  # css selector use for matching first element and return   
        or soup.select_one("article")
        or soup.select_one("main")
    )

    if container is None:
        raise ValueError("Content container not found")


# Unnecessary HTML elements remove karna
    for tag in container.select(
        "script, style, noscript, nav, footer, "
        "header, img, svg, iframe, form, "
        ".breadcrumb, .sidebar"
    ):
        tag.decompose()

    blocks = []
    seen = set()

# duplicate content ko avoid karna
    def add_block(block):
        key = (
            block["type"],
            clean(block.get("text", "")).casefold()
            if "text" in block
            else json.dumps(block["rows"], ensure_ascii=False)
        )

        if key not in seen:
            seen.add(key)
            blocks.append(block)

    # Read meaningful leaf-level content
    for element in container.descendants:
        if not isinstance(element, Tag):
            continue

        if element.name == "table":
            rows = []

            for tr in element.find_all("tr"):
                cells = [
                    clean(cell.get_text(" ", strip=True))
                    for cell in tr.find_all(["th", "td"], recursive=False)
                ]
                if cells:
                    rows.append(cells)

            if rows:
                add_block({"type": "table", "rows": rows})
            continue

        if element.find_parent("table"):
            continue

        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6") or "content-title" in element.get("class", []):
            
            text = clean(element.get_text(" ", strip=True))
            if text:
                add_block({
                    "type": "heading",
                   "level": int(element.name[1]) if element.name.startswith("h") else 3,
                    "text": text
                })
            continue

        if element.name == "li":
            text = clean(element.get_text(" ", strip=True))
            if text:
                add_block({"type": "list_item", "text": text})
            continue

        if element.name in ("p", "div", "span"):
            if element.find(["p", "div", "section", "table", "ul", "ol"]):
                continue

            text = clean(element.get_text(" ", strip=True))

            if len(text) >= 15:
                add_block({"type": "paragraph", "text": text})

    return blocks

results = []

for page in TEST_PAGES:
    print("\nChecking:", page["title"])

    try:
        blocks = extract_content(page["url"])

        results.append({
            "title": page["title"],
            "source_url": page["url"],
            "blocks": blocks
        })

        print("Extracted blocks:", len(blocks))

        for block in blocks[:8]:
            print(
                block["type"],
                block.get("text", "[TABLE]")[:120]
            )

    except Exception as error:
        print("ERROR:", error)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", encoding="utf-8") as file:
    json.dump(results, file, indent=2, ensure_ascii=False)

print("\nSaved:", OUTPUT)
