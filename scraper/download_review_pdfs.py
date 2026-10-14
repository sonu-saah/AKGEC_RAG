import json
import hashlib
import time
from pathlib import Path

import requests

from scraper.resource_downloader import download_pdf, OUTPUT_DIR, USER_AGENT

INPUT = Path("data/fresh/approved_review_pdfs.json")
REPORT = Path("data/fresh/review_download_report.json")

with INPUT.open(encoding="utf-8") as f:
    data = json.load(f)

resources = data["documents"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

results = []

print("Selected PDFs:", len(resources))

for i, resource in enumerate(resources, 1):
    print(f"\n[{i}/{len(resources)}] {resource['title']}")

    status, message, path = download_pdf(session, resource)

    result = {
        **resource,
        "status": status,
        "message": message,
        "local_path": str(path) if path else None
    }

    if path and path.exists():
        result["file_size_bytes"] = path.stat().st_size
        result["sha256"] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

    results.append(result)

    print("Status:", status)
    print("Message:", message)

    if status == "downloaded":
        time.sleep(1)

report = {
    "total_resources": len(resources),
    "downloaded": sum(r["status"] == "downloaded" for r in results),
    "existing": sum(r["status"] == "existing" for r in results),
    "skipped": sum(r["status"] == "skipped" for r in results),
    "failed": sum(r["status"] == "failed" for r in results),
    "results": results
}

with REPORT.open("w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\nREVIEW PDF DOWNLOAD COMPLETED")
print("Downloaded:", report["downloaded"])
print("Existing:", report["existing"])
print("Skipped:", report["skipped"])
print("Failed:", report["failed"])
print("Report:", REPORT)
