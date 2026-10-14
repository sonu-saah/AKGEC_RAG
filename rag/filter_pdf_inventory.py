
# Classify discovered AKGEC PDFs by relevance

import json
from pathlib import Path
from collections import Counter


# Input and output files
INPUT_FILE = Path("data/fresh/resource_urls.json")
OUTPUT_FILE = Path("data/fresh/filtered_pdf_inventory.json")


# High-priority college information
ESSENTIAL_KEYWORDS = [
    "academic-calendar",
    "academic-calender",
    "list-of-holidays",
    "hostelfee",
    "nirf2026",
    "mandatory-disclosure",
    "aicteapprovalyear-2026",
    "visitedcompanysummary",
    "naac-certificate",
]

# Documents requiring manual review
REVIEW_KEYWORDS = [
    "policy",
    "guidelines",
    "service-rules",
    "delegation-of-powers",
    "annual-report",
    "aqar",
    "student-satisfaction",
    "course",
    "syllabus",
    "sampark",
    "magazine",
    "valueeducation",
    "emergence",
    "recruitment",
]

# Potentially personal or sensitive records
EXCLUDED_KEYWORDS = [
    "selected-students",
    "nptel-certificates",
    "1.2.2certis",
    "1.3.2-certificates",
    "certificates-5.3.1",
]

# Admission fee documents with generic filenames
ADMISSION_FEE_KEYWORDS = [
    "btech1yr",
    "b.tech1yr",
    "b.techii",
    "b-tech-iind",
    "mca1yr",
    "mca-ii-year",
    "hostelfee",
]


def classify_pdf(resource):
    title = resource.get("title", "")
    url = resource.get("url", "")
    section = resource.get("section", "")

    filename = Path(url.split("?")[0]).name
    searchable_text = (title + " " + filename).lower()

    # Exclude potentially personal records first
    if any(word in searchable_text for word in EXCLUDED_KEYWORDS):
        return "excluded", "Potential personal/student records"

    # Research publications are not core college information
    if section == "COLLEGE PUBLICATIONS":
        if "sampark" in searchable_text:
            return "review", "College magazine requires review"

        return "optional", "Research publication or article"

    # Identify admission fee documents
    if section == "ADMISSIONS":
        if any(word in searchable_text for word in ADMISSION_FEE_KEYWORDS):
            return "essential", "Admission or hostel fee structure"

    # Core college documents
    if any(word in searchable_text for word in ESSENTIAL_KEYWORDS):
        return "essential", "Core college information"

    # Documents requiring review
    if any(word in searchable_text for word in REVIEW_KEYWORDS):
        return "review", "Requires content review"

    # IQAC supporting documents
    if section == "IQAC":
        return "review", "IQAC supporting document"

    # Historical institutional records
    if section == "ABOUT":
        return "review", "Institutional document or historical record"

    return "review", "Relevance requires manual verification"


def main():
    if not INPUT_FILE.exists():
        print("Input file missing:", INPUT_FILE)
        return

    # Load discovered resources
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    inventory = []
    seen_urls = set()

    # Filter PDF resources
    for resource in data.get("resources", []):
        if resource.get("file_type", "").lower() != ".pdf":
            continue

        url = resource.get("url", "")

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        category, reason = classify_pdf(resource)

        inventory.append({
            "title": resource.get("title", ""),
            "url": url,
            "source_page": resource.get("source_page", ""),
            "section": resource.get("section", ""),
            "file_type": ".pdf",
            "category": category,
            "reason": reason
        })

    # Count documents by category
    counts = Counter(
        item["category"] for item in inventory
    )

    # Prepare final report
    report = {
        "total_pdfs": len(inventory),
        "category_counts": {
            category: counts.get(category, 0)
            for category in [
                "essential",
                "review",
                "optional",
                "excluded"
            ]
        },
        "documents": inventory
    }

    # Save inventory
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("=" * 50)
    print("AKGEC PDF FILTERING COMPLETED")
    print("=" * 50)

    print("Total PDFs:", len(inventory))

    for category, count in report["category_counts"].items():
        print(f"{category.upper()}: {count}")

    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
