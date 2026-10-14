# Extract structured content from AKGEC webpages

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag


OUTPUT_DIR = Path("data/fresh/pages")

HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}

REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "header",
    "nav",
    "footer",
    "form",
    "aside",
    "iframe",
]

BLOCK_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "li", "table"
]


# Clean extra spaces without joining separate paragraphs
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


# Extract a table row by row
def extract_table(table):
    rows = []

    for tr in table.find_all("tr"):
        cells = [
            clean_text(cell.get_text(" ", strip=True))
            for cell in tr.find_all(["th", "td"], recursive=False)
        ]

        if cells:
            rows.append(" | ".join(cells))

    return "\n".join(rows)


# Find main content area
def find_main_content(soup):
    for selector in [
        "main",
        "article",
        ".entry-content",
        ".elementor-widget-theme-post-content",
        ".page-content",
    ]:
        content = soup.select_one(selector)

        if content and clean_text(content.get_text(" ", strip=True)):
            return content

    return soup.body


# Extract structured blocks, including div-based content
def extract_blocks(content):
    blocks = []

    if content is None:
        return blocks

    # These elements directly represent meaningful content
    meaningful_tags = {
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "li", "table"
    }

    for element in content.descendants:
        if not isinstance(element, Tag):
            continue

        tag = element.name

        if tag in meaningful_tags:
            if element.find_parent(["p", "li", "table"]):
                continue

            if tag == "table":
                text = extract_table(element)
                block_type = "table"

            else:
                text = clean_text(element.get_text(" ", strip=True))
                block_type = (
                    "heading" if tag.startswith("h")
                    else "list_item" if tag == "li"
                    else "paragraph"
                )

        elif tag == "div":
            # Extract only leaf divs to avoid duplicate parent content
            if element.find(
                ["div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "table"]
            ):
                continue

            text = clean_text(element.get_text(" ", strip=True))
            block_type = "paragraph"

        else:
            continue

        if not text:
            continue

        # Avoid consecutive duplicate blocks
        if blocks and blocks[-1]["text"] == text:
            continue

        blocks.append({
            "type": block_type,
            "tag": tag,
            "text": text
        })

    return blocks

# Convert blocks into readable text
def format_blocks(blocks):
    lines = []

    for block in blocks:
        text = block["text"]

        if block["type"] == "heading":
            lines.append(f"\n{text.upper()}\n")

        elif block["type"] == "list_item":
            lines.append(f"- {text}")

        else:
            lines.append(text)

    return "\n\n".join(lines).strip()


# Extract one webpage
def extract_page(url, section="UNCLASSIFIED"):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = (
        clean_text(soup.title.get_text(" ", strip=True))
        if soup.title
        else ""
    )

    for tag in soup(REMOVE_TAGS):
        tag.decompose()

    content = find_main_content(soup)
    blocks = extract_blocks(content)
    text = format_blocks(blocks)

    return {
        "title": title,
        "url": response.url,
        "section": section,
        "blocks": blocks,
        "text": text,
        "character_count": len(text)
    }


# Save extracted page as JSON
def save_page(page_data, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / filename

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            page_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return output_file


# Test only one AKGEC page
def main():
    url = "https://www.akgec.ac.in/vision-and-mission/"

    page_data = extract_page(
        url,
        section="ABOUT"
    )

    output_file = save_page(
        page_data,
        "vision-and-mission.json"
    )

    print("Status: SUCCESS")
    print("Title:", page_data["title"])
    print("Section:", page_data["section"])
    print("Total blocks:", len(page_data["blocks"]))
    print("Text length:", page_data["character_count"])
    print("Output:", output_file)

    print("\nFIRST 1500 CHARACTERS:\n")
    print(page_data["text"][:1500])


if __name__ == "__main__":
    main()