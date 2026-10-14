# AKGEC selective website crawler

import json
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse, urldefrag
from urllib.robotparser import RobotFileParser

import requests

from page_text import extract_page, save_page


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_URL = "https://www.akgec.ac.in"

OUTPUT_DIR = Path("data/fresh/pages")
REPORT_FILE = Path("data/fresh/crawl_report.json")

REQUEST_DELAY = 1.0

USER_AGENT = "AKGEC-RAG-Research-Bot/1.0"

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in"
}

# Pilot mode: only selected pages
PILOT_MODE = True


# --------------------------------------------------
# Selected official AKGEC pages
# --------------------------------------------------

SECTION_URLS = {
    "ABOUT": [
        "/vision-and-mission/",
        "/about/director_akgec/",
        "/about/management/",
    ],

    "DEPARTMENTS": [
        "/departments/computer-science-and-engineering/",
    ],

    "ACADEMICS": [
        "/academics/academic-calendar/",
    ],

    "ADMISSIONS": [
        "/courses-offered/",
        "/fee-structure-for-new-students2026-27/",
    ],

    "PLACEMENTS": [
        "/placements/placement-records/",
    ],
}


# --------------------------------------------------
# Normalize URL
# --------------------------------------------------

def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    domain = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"

    return f"https://{domain}{path}"


# --------------------------------------------------
# Validate domain
# --------------------------------------------------

def is_allowed_url(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in ALLOWED_DOMAINS
    )


# --------------------------------------------------
# Robots.txt configuration
# --------------------------------------------------

def load_robots():
    robots = RobotFileParser()
    robots.set_url(f"{BASE_URL}/robots.txt")

    try:
        response = requests.get(
            robots.url,
            timeout=15,
            headers={"User-Agent": USER_AGENT}
        )
        response.raise_for_status()

        robots.parse(response.text.splitlines())

        return robots

    except requests.RequestException as error:
        print("Could not verify robots.txt:", error)
        return None


# --------------------------------------------------
# Generate unique filename
# --------------------------------------------------

def create_filename(url):
    parsed = urlparse(url)

    path = parsed.path.strip("/").replace("/", "_")

    if not path:
        path = "homepage"

    url_hash = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:10]

    return f"{path}_{url_hash}.json"


# --------------------------------------------------
# Build selected URL list
# --------------------------------------------------

def build_url_list():
    selected = []
    seen = set()

    for section, paths in SECTION_URLS.items():
        for path in paths:
            url = normalize_url(BASE_URL + path)

            if url in seen:
                continue

            seen.add(url)

            selected.append({
                "section": section,
                "url": url
            })

    return selected


# --------------------------------------------------
# Main crawler
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    selected_pages = build_url_list()

    robots = load_robots()

    if robots is None:
        print("Crawler stopped: robots.txt not verified.")
        return

    successful = []
    failed = []
    skipped = []

    seen_content = set()

    print("PILOT MODE:", PILOT_MODE)
    print("Selected pages:", len(selected_pages))

    for index, item in enumerate(selected_pages, start=1):
        section = item["section"]
        url = item["url"]

        print(f"\n[{index}/{len(selected_pages)}] {section}")
        print(url)

        if not is_allowed_url(url):
            skipped.append({
                "url": url,
                "reason": "Domain not allowed"
            })
            continue

        if not robots.can_fetch(USER_AGENT, url):
            skipped.append({
                "url": url,
                "reason": "Blocked by robots.txt"
            })
            continue

        try:
            page_data = extract_page(
                url,
                section=section
            )

            text = page_data["text"].strip()

            if len(text) < 80:
                skipped.append({
                    "url": url,
                    "reason": "Very short extracted content",
                    "character_count": len(text)
                })
                print("Skipped: Very short content")
                continue

            content_hash = hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest()

            if content_hash in seen_content:
                skipped.append({
                    "url": url,
                    "reason": "Duplicate content"
                })
                print("Skipped: Duplicate content")
                continue

            seen_content.add(content_hash)

            filename = create_filename(url)

            output_file = save_page(
                page_data,
                filename
            )

            successful.append({
                "section": section,
                "url": url,
                "file": str(output_file),
                "characters": len(text),
                "blocks": len(page_data["blocks"])
            })

            print("Saved:", output_file)
            print("Characters:", len(text))
            print("Blocks:", len(page_data["blocks"]))

        except Exception as error:
            failed.append({
                "url": url,
                "error": str(error)
            })

            print("Failed:", error)

        time.sleep(REQUEST_DELAY)

    report = {
        "pilot_mode": PILOT_MODE,
        "selected_pages": len(selected_pages),
        "successful": successful,
        "failed": failed,
        "skipped": skipped
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 55)
    print("AKGEC PILOT CRAWL COMPLETED")
    print("=" * 55)
    print("Successful:", len(successful))
    print("Failed:", len(failed))
    print("Skipped:", len(skipped))
    print("Report:", REPORT_FILE)


if __name__ == "__main__":
    main()