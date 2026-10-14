# Discover PDF and image resources from AKGEC navigation pages

import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


# Configuration
NAVIGATION_FILE = Path("data/fresh/navigation_urls.json")
OUTPUT_FILE = Path("data/fresh/resource_urls.json")

BASE_URL = "https://www.akgec.ac.in"
USER_AGENT = "AKGEC-RAG-Research-Bot/1.0"

HEADERS = {"User-Agent": USER_AGENT}

REQUEST_DELAY = 1.5

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in"
}

RESOURCE_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


# Normalize URLs without fragments
def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    return parsed._replace(fragment="").geturl()


# Check allowed official domain
def is_allowed_domain(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in ALLOWED_DOMAINS
    )


# Load robots.txt
def load_robots():
    robots = RobotFileParser()
    robots.set_url(f"{BASE_URL}/robots.txt")

    try:
        response = requests.get(
            robots.url,
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

        robots.parse(response.text.splitlines())
        return robots

    except requests.RequestException as error:
        print("Robots verification failed:", error)
        return None


# Read all discovered navigation pages
def load_pages():
    with open(
        NAVIGATION_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        data = json.load(file)

    pages = []
    seen = set()

    for item in data.get("pages", []):
        url = normalize_url(item.get("url", ""))

        if not is_allowed_domain(url):
            continue

        if url in seen:
            continue

        seen.add(url)

        pages.append({
            "url": url,
            "section": item.get("section", "UNCLASSIFIED"),
            "title": item.get("title", "")
        })

    return pages


# Discover resource links from webpage
def extract_resources(page):
    page_url = page["url"]

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=25
    )

    response.raise_for_status()

    if not is_allowed_domain(response.url):
        raise ValueError("Redirected outside allowed domain")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove website navigation and footer
    for tag in soup(["header", "nav", "footer", "script", "style"]):
        tag.decompose()

    content = soup.select_one("main") or soup.body

    if content is None:
        return []

    resources = []

    # PDF and image links
    for tag in content.select("a[href]"):
        url = normalize_url(
            urljoin(response.url, tag["href"])
        )

        extension = Path(urlparse(url).path.lower()).suffix

        if not is_allowed_domain(url):
            continue

        if extension not in RESOURCE_EXTENSIONS:
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
            "file_type": extension
        })

    # Embedded images
    for tag in content.select("img[src]"):
        url = normalize_url(
            urljoin(response.url, tag["src"])
        )

        extension = Path(urlparse(url).path.lower()).suffix

        if not is_allowed_domain(url):
            continue

        if extension not in RESOURCE_EXTENSIONS:
            continue

        title = tag.get("alt", "").strip()

        if not title:
            title = Path(urlparse(url).path).stem

        resources.append({
            "title": title,
            "url": url,
            "source_page": page_url,
            "section": page["section"],
            "page_title": page["title"],
            "file_type": extension
        })

    return resources


# Main resource discovery
def main():
    if not NAVIGATION_FILE.exists():
        print("Navigation file missing:", NAVIGATION_FILE)
        return

    robots = load_robots()

    if robots is None:
        print("Discovery stopped: robots.txt not verified.")
        return

    pages = load_pages()

    print("Navigation pages:", len(pages))

    all_resources = {}
    failed_pages = []
    skipped_pages = []

    for index, page in enumerate(pages, start=1):
        url = page["url"]

        print(f"[{index}/{len(pages)}] {url}")

        if not robots.can_fetch(USER_AGENT, url):
            skipped_pages.append({
                "url": url,
                "reason": "Blocked by robots.txt"
            })
            continue

        try:
            resources = extract_resources(page)

            for resource in resources:
                resource_url = resource["url"]

                if resource_url not in all_resources:
                    all_resources[resource_url] = resource

            print("Resources found:", len(resources))

        except (requests.RequestException, ValueError) as error:
            failed_pages.append({
                "url": url,
                "error": str(error)
            })
            print("Failed:", error)

        finally:
            time.sleep(REQUEST_DELAY)

    resource_list = list(all_resources.values())

    report = {
        "pages_scanned": len(pages),
        "total_resources": len(resource_list),
        "resources": resource_list,
        "failed_pages": failed_pages,
        "skipped_pages": skipped_pages
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    pdf_count = sum(
        r["file_type"] == ".pdf"
        for r in resource_list
    )

    image_count = sum(
        r["file_type"] != ".pdf"
        for r in resource_list
    )

    print("\n" + "=" * 55)
    print("RESOURCE DISCOVERY COMPLETED")
    print("=" * 55)

    print("Pages scanned:", len(pages))
    print("Unique PDFs:", pdf_count)
    print("Unique images:", image_count)
    print("Failed pages:", len(failed_pages))
    print("Skipped pages:", len(skipped_pages))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()