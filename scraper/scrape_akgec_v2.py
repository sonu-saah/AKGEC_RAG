
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

INPUT = Path("data/selected_urls.json")
OUTPUT = Path("data/akgec_structured_v2.json")
REPORT = Path("data/scraping_v2_report.json")

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Normalize whitespace in extracted text.
def clean(text):
    return re.sub(r"\s+", " ", text).strip()

# Identify headings including custom AKGEC title elements.
def is_heading(tag):
    if re.fullmatch(r"h[1-6]", tag.name or ""):
        return True

    classes = tag.get("class", [])

    return "content-title" in classes

# Extract table rows while preserving cell order.
def extract_table(table):
    rows = []

    for tr in table.find_all("tr"):
        cells = [
            clean(cell.get_text(" ", strip=True))
            for cell in tr.find_all(["th", "td"], recursive=False)
        ]

        if cells:
            rows.append(cells)

    return rows

# Extract structured text from a single HTML page.
def extract_page(url):
    response = session.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    container = (
        soup.select_one(".entry-content")
        or soup.select_one("article")
        or soup.select_one("main")
    )

    if container is None:
        raise ValueError("Content container not found")

    for tag in container.select(
        "script, style, noscript, nav, footer, "
        "header, iframe, form, svg, img, "
        ".breadcrumb, .sidebar"
    ):
        tag.decompose()

    blocks = []
    seen = set()

    for element in container.descendants:
        if not isinstance(element, Tag):
            continue

        if element.name == "table":
            rows = extract_table(element)

            if rows:
                key = json.dumps(rows, ensure_ascii=False)

                if key not in seen:
                    seen.add(key)
                    blocks.append({
                        "type": "table",
                        "rows": rows
                    })
            continue

        if element.find_parent("table"):
            continue

        if is_heading(element):
            text = clean(element.get_text(" ", strip=True))

            if not text:
                continue

            level = (
                int(element.name[1])
                if re.fullmatch(r"h[1-6]", element.name)
                else 3
            )

            block = {
                "type": "heading",
                "level": level,
                "text": text
            }

        elif element.name == "li":
            text = clean(element.get_text(" ", strip=True))

            if not text:
                continue

            block = {
                "type": "list_item",
                "text": text
            }

        elif element.name in ("p", "div", "span"):
            if element.find(
                ["p", "div", "section", "table", "ul", "ol"]
            ):
                continue

            text = clean(element.get_text(" ", strip=True))

            if len(text) < 15:
                continue

            block = {
                "type": "paragraph",
                "text": text
            }

        else:
            continue

        key = (
            block["type"],
            block["text"].casefold()
        )

        if key in seen:
            continue

        seen.add(key)
        blocks.append(block)

    return blocks

# Keep only the three approved Central Library subsections.
def filter_library(blocks):
    approved = {
        "about akgec central library",
        "library team",
        "contact us"
    }

    result = []
    active = False

    for block in blocks:
        if block["type"] == "heading":
            title = block["text"].casefold()
            active = title in approved

        if active:
            result.append(block)

    return result

# Remove tables explicitly labeled for the 2025-26 session.
def filter_old_fee_tables(blocks):
    result = []

    for block in blocks:
        if block["type"] == "table":
            content = " ".join(
                " ".join(row)
                for row in block["rows"]
            ).lower()

            if "2025-26" in content:
                continue

        result.append(block)

    return result

# Scrape all selected pages and save structured results.
def main():
    pages = json.loads(INPUT.read_text(encoding="utf-8"))

    results = []
    errors = []

    for index, page in enumerate(pages, 1):
        print(
            f"[{index}/{len(pages)}] {page['title']}",
            flush=True
        )

        try:
            blocks = extract_page(page["url"])

            if page["title"] == "Library":
                blocks = filter_library(blocks)

            if page["title"] == "Fee Structure for New Students":
                blocks = filter_old_fee_tables(blocks)

            if not blocks:
                raise ValueError("No content extracted")

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

    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    report = {
        "selected_urls": len(pages),
        "extracted_pages": len(results),
        "errors": errors,
        "missing_topics": [
            "Admission Enquiry Form details",
            "2026 syllabus",
            "Academic fees contained in linked PDFs",
            "Department subpage completeness"
        ]
    }

    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== V2 SCRAPING REPORT =====")
    print("Selected URLs:", len(pages))
    print("Extracted pages:", len(results))
    print("Errors:", len(errors))
    print("Output:", OUTPUT)
    print("Report:", REPORT)


if __name__ == "__main__":
    main()
