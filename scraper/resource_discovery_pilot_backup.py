# Discover PDF resources from selected AKGEC webpages

import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup


# Configuration
PAGES_DIR = Path("data/fresh/pages")
OUTPUT_FILE = Path("data/fresh/resource_urls.json")

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in",
    "admissions.akgec.ac.in"
}

HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}

REQUEST_DELAY = 1.0

RESOURCE_EXTENSIONS = {".pdf"}

# Only these sections are included in the pilot
ALLOWED_SECTIONS = {
    "ABOUT",
    "DEPARTMENTS",
    "ACADEMICS",
    "ADMISSIONS",
    "PLACEMENTS"
}


# Normalize URL and remove fragments
def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    domain = parsed.netloc.lower()
    path = parsed.path

    return f"https://{domain}{path}"


# Check allowed domain
def is_allowed_domain(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in ALLOWED_DOMAINS
    )


# Check PDF extension
def is_pdf(url):
    return Path(urlparse(url).path.lower()).suffix == ".pdf"


# Load unique pages from fresh dataset
def load_pages():
    pages = []
    seen_urls = set()

    for file in sorted(PAGES_DIR.glob("*.json")):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        url = data.get("url", "")
        section = data.get("section", "")

        if (
            section not in ALLOWED_SECTIONS
            or not url
            or url in seen_urls
        ):
            continue

        seen_urls.add(url)

        pages.append({
            "url": url,
            "section": section,
            "title": data.get("title", "")
        })

    return pages


# Discover PDFs from a selected webpage
def extract_resources(page):
    page_url = page["url"]

    print("Scanning:", page_url)

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.select_one("main") or soup.body

    if content is None:
        return []

    resources = []

    for tag in content.select("a[href]"):
        url = normalize_url(
            urljoin(page_url, tag["href"])
        )

        if not is_allowed_domain(url):
            continue

        if not is_pdf(url):
            continue

        title = tag.get_text(" ", strip=True)

        if not title:
            title = Path(urlparse(url).path).stem

        resources.append({
            "title": title,
            "url": url,
            "source_page": page_url,
            "section": page["section"],
            "page_title": page["title"],
            "file_type": ".pdf"
        })

    return resources


# Main resource discovery
def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    pages = load_pages()

    print("Selected pages:", len(pages))

    all_resources = {}
    failed_pages = []

    for page in pages:
        try:
            resources = extract_resources(page)

            for resource in resources:
                url = resource["url"]

                if url not in all_resources:
                    all_resources[url] = resource

            print("PDFs found:", len(resources))

        except requests.RequestException as error:
            failed_pages.append({
                "url": page["url"],
                "error": str(error)
            })
            print("Request failed:", error)

        time.sleep(REQUEST_DELAY)

    resource_list = list(all_resources.values())

    report = {
        "pages_scanned": len(pages),
        "total_resources": len(resource_list),
        "resources": resource_list,
        "failed_pages": failed_pages
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 55)
    print("PDF RESOURCE DISCOVERY COMPLETED")
    print("=" * 55)
    print("Pages scanned:", len(pages))
    print("Unique PDFs:", len(resource_list))
    print("Failed pages:", len(failed_pages))
    print("Output:", OUTPUT_FILE)

    print("\nDISCOVERED PDFs:")
    for resource in resource_list:
        print(
            f"[{resource['section']}] "
            f"{resource['title']} -> {resource['url']}"
        )


if __name__ == "__main__":
    main()