# Download selected AKGEC PDF resources safely

import json
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


# Configuration
INPUT_FILE = Path("data/fresh/filtered_pdf_inventory.json")
OUTPUT_DIR = Path("data/fresh/resources")
REPORT_FILE = Path("data/fresh/download_report.json")

USER_AGENT = "AKGEC-RAG-Research-Bot/1.0"
REQUEST_DELAY = 1.0
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in"
}

# Large magazine excluded during pilot
SKIP_FILENAMES = {
    "Magazine-CSE.pdf"
}


# Check URL
def is_allowed_url(url):
    parsed = urlparse(url)

    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_DOMAINS
        and parsed.path.lower().endswith(".pdf")
    )


# Generate collision-resistant filename
def make_filename(url):
    original_name = Path(urlparse(url).path).name

    url_hash = hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:10]

    return f"{url_hash}_{original_name}"


# Check existing PDF validity
def valid_pdf(path):
    try:
        if not path.is_file() or path.stat().st_size < 5:
            return False

        with open(path, "rb") as file:
            return file.read(5) == b"%PDF-"

    except OSError:
        return False


# Download one PDF
def download_pdf(session, resource):
    url = resource["url"]

    if not is_allowed_url(url):
        return "skipped", "Invalid or disallowed URL", None

    original_name = Path(urlparse(url).path).name

    if original_name in SKIP_FILENAMES:
        return "skipped", "Excluded large magazine", None

    filename = make_filename(url)
    destination = OUTPUT_DIR / filename

    if destination.exists():
        if valid_pdf(destination):
            return "existing", "Already downloaded", destination

        destination.unlink()

    temp_file = OUTPUT_DIR / f"{filename}.part"

    try:
        with session.get(
            url,
            stream=True,
            timeout=(10, 45),
            allow_redirects=True
        ) as response:

            response.raise_for_status()

            if not is_allowed_url(response.url):
                return "skipped", "Redirected to disallowed URL", None

            declared_size = int(
                response.headers.get("Content-Length", "0")
            )

            if declared_size > MAX_FILE_SIZE:
                return "skipped", "File exceeds size limit", None

            total_bytes = 0

            with open(temp_file, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=64 * 1024
                ):
                    if not chunk:
                        continue

                    total_bytes += len(chunk)

                    if total_bytes > MAX_FILE_SIZE:
                        return "skipped", "File exceeds size limit", None

                    file.write(chunk)

        if not valid_pdf(temp_file):
            return "failed", "Downloaded file is not a valid PDF", None

        temp_file.replace(destination)

        return "downloaded", "Success", destination

    except requests.RequestException as error:
        return "failed", str(error), None

    except (OSError, ValueError) as error:
        return "failed", str(error), None

    finally:
        if temp_file.exists():
            temp_file.unlink()


# Main downloader
def main():
    if not INPUT_FILE.exists():
        print("Resource list not found:", INPUT_FILE)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    resources = [
    resource
    for resource in data.get("documents", [])
    if resource.get("category") == "essential"
]

    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT
    })

    results = []

    print("Resources discovered:", len(resources))

    for index, resource in enumerate(resources, start=1):
        print(
            f"\n[{index}/{len(resources)}] "
            f"{resource['section']} | {resource['title']}"
        )

        status, message, file_path = download_pdf(
            session,
            resource
        )

        result = {
            **resource,
            "status": status,
            "message": message,
            "local_path": str(file_path) if file_path else None
        }

        if file_path and file_path.exists():
            result["file_size_bytes"] = file_path.stat().st_size
            result["sha256"] = hashlib.sha256(
                file_path.read_bytes()
            ).hexdigest()

        results.append(result)

        print("Status:", status)
        print("Message:", message)

        if file_path:
            print("File:", file_path)

        if status == "downloaded":
            time.sleep(REQUEST_DELAY)

    report = {
        "total_resources": len(resources),
        "downloaded": sum(
            r["status"] == "downloaded" for r in results
        ),
        "existing": sum(
            r["status"] == "existing" for r in results
        ),
        "skipped": sum(
            r["status"] == "skipped" for r in results
        ),
        "failed": sum(
            r["status"] == "failed" for r in results
        ),
        "results": results
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 55)
    print("PDF DOWNLOAD COMPLETED")
    print("=" * 55)

    print("Downloaded:", report["downloaded"])
    print("Existing:", report["existing"])
    print("Skipped:", report["skipped"])
    print("Failed:", report["failed"])
    print("Report:", REPORT_FILE)


if __name__ == "__main__":
    main()