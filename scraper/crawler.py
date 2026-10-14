# AKGEC section-wise website crawler

import json
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests

from page_text import extract_page, save_page


# Configuration
BASE_URL = "https://www.akgec.ac.in"

NAVIGATION_FILE = Path("data/fresh/navigation_urls.json")
OUTPUT_DIR = Path("data/fresh/pages")
REPORT_FILE = Path("data/fresh/crawl_report.json")

USER_AGENT = "AKGEC-RAG-Research-Bot/1.0"

REQUEST_DELAY = 1.5
MIN_TEXT_LENGTH = 80

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in"
}

# First test 5 new pages, then enable full crawl
TEST_MODE = False
TEST_LIMIT = 5


# Normalize URLs consistently
def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    path = parsed.path.rstrip("/") or "/"

    return f"https://www.akgec.ac.in{path}"


# Check official domain
def is_allowed_url(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in ALLOWED_DOMAINS
        and not parsed.query
    )


# Load robots.txt
def load_robots():
    robots = RobotFileParser()
    robots.set_url(f"{BASE_URL}/robots.txt")

    try:
        response = requests.get(
            robots.url,
            headers={"User-Agent": USER_AGENT},
            timeout=20
        )
        response.raise_for_status()

        robots.parse(response.text.splitlines())
        return robots

    except requests.RequestException as error:
        print("Robots verification failed:", error)
        return None


# Stable filename for each URL
def create_filename(url):
    parsed = urlparse(url)

    path = parsed.path.strip("/").replace("/", "_")

    if not path:
        path = "homepage"

    url_hash = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:10]

    return f"{path}_{url_hash}.json"


# Load existing pages and content hashes
def load_existing_pages():
    existing_urls = set()
    existing_hashes = set()

    for file in OUTPUT_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as handle:
                page = json.load(handle)

            url = page.get("url", "")

            if url:
                existing_urls.add(normalize_url(url))

            text = page.get("text", "").strip()

            if text:
                existing_hashes.add(
                    hashlib.sha256(
                        text.encode("utf-8")
                    ).hexdigest()
                )

        except (OSError, ValueError) as error:
            print("Could not read:", file, error)

    return existing_urls, existing_hashes


# Read discovered navigation URLs
def load_navigation_urls():
    with open(
        NAVIGATION_FILE,
        "r",
        encoding="utf-8"
    ) as handle:
        data = json.load(handle)

    selected = []
    seen = set()

    for item in data.get("pages", []):
        url = item.get("url", "")

        if not is_allowed_url(url):
            continue

        normalized = normalize_url(url)

        if normalized in seen:
            continue

        seen.add(normalized)

        selected.append({
            "section": item.get("section", "UNCLASSIFIED"),
            "title": item.get("title", ""),
            "url": normalized
        })

    return selected


# Main crawler
def main():
    if not NAVIGATION_FILE.exists():
        print("Navigation file missing:", NAVIGATION_FILE)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    robots = load_robots()

    if robots is None:
        print("Crawler stopped for safety.")
        return

    selected = load_navigation_urls()

    existing_urls, existing_hashes = load_existing_pages()

    new_pages = [
        item for item in selected
        if item["url"] not in existing_urls
    ]

    if TEST_MODE:
        new_pages = new_pages[:TEST_LIMIT]

    successful = []
    failed = []
    skipped = []

    print("=" * 55)
    print("AKGEC SECTION-WISE CRAWLER")
    print("=" * 55)
    print("Test mode:", TEST_MODE)
    print("Navigation URLs:", len(selected))
    print("Existing URLs:", len(existing_urls))
    print("Pages selected for this run:", len(new_pages))

    for index, item in enumerate(new_pages, start=1):
        section = item["section"]
        url = item["url"]

        print(f"\n[{index}/{len(new_pages)}] {section}")
        print(url)

        if not robots.can_fetch(USER_AGENT, url):
            skipped.append({
                "url": url,
                "section": section,
                "reason": "Blocked by robots.txt"
            })
            print("Skipped: robots.txt")
            continue

        try:
            page_data = extract_page(
                url,
                section=section
            )

            # Reject redirects to unrelated domains
            final_url = page_data.get("url", url)

            if not is_allowed_url(final_url):
                skipped.append({
                    "url": url,
                    "reason": "Redirected outside allowed domain"
                })
                continue

            text = page_data.get("text", "").strip()

            if len(text) < MIN_TEXT_LENGTH:
                skipped.append({
                    "url": url,
                    "section": section,
                    "reason": "Short content",
                    "characters": len(text)
                })
                print("Skipped: short content")
                continue

            content_hash = hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest()

            if content_hash in existing_hashes:
                skipped.append({
                    "url": url,
                    "section": section,
                    "reason": "Duplicate content"
                })
                print("Skipped: duplicate content")
                continue

            existing_hashes.add(content_hash)

            filename = create_filename(url)
            output_file = OUTPUT_DIR / filename

            if output_file.exists():
                skipped.append({
                    "url": url,
                    "reason": "Output file already exists"
                })
                continue

            saved_file = save_page(
                page_data,
                filename
            )

            existing_urls.add(normalize_url(final_url))

            successful.append({
                "section": section,
                "title": item["title"],
                "url": final_url,
                "file": str(saved_file),
                "characters": len(text),
                "blocks": len(page_data.get("blocks", []))
            })

            print("Saved:", saved_file)
            print("Characters:", len(text))

        except Exception as error:
            failed.append({
                "section": section,
                "url": url,
                "error": str(error)
            })

            print("Failed:", error)

        finally:
            time.sleep(REQUEST_DELAY)

    report = {
        "test_mode": TEST_MODE,
        "navigation_urls": len(selected),
        "existing_urls_before_run": len(existing_urls) - len(successful),
        "attempted": len(new_pages),
        "successful": successful,
        "failed": failed,
        "skipped": skipped
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as handle:
        json.dump(
            report,
            handle,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 55)
    print("CRAWL COMPLETED")
    print("=" * 55)
    print("Saved:", len(successful))
    print("Failed:", len(failed))
    print("Skipped:", len(skipped))
    print("Report:", REPORT_FILE)


if __name__ == "__main__":
    main()