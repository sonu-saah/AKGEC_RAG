import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from pathlib import Path
import json
import time


# ---------------------------------------------------------
# Website configuration
# ---------------------------------------------------------
# Ye AKGEC ke important official domains hain.
# Hum external/random websites ko crawl nahi karenge.
ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in",
    "admissions.akgec.ac.in"
}


# ---------------------------------------------------------
# Starting pages
# ---------------------------------------------------------
# In pages se resource URLs discover karna start hoga.
START_URLS = [
    "https://www.akgec.ac.in/"
]


# ---------------------------------------------------------
# Resource file extensions
# ---------------------------------------------------------
# Ye downloadable document formats hain
# jo future RAG pipeline mein useful ho sakte hain.
RESOURCE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx"
}


# ---------------------------------------------------------
# Output location
# ---------------------------------------------------------
# Discovered resources ko JSON mein save karenge.
OUTPUT_PATH = Path("data/resource_urls.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------
# User-Agent website ko batata hai ki request kis client
# se aa rahi hai.
HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}


# ---------------------------------------------------------
# URL normalization
# ---------------------------------------------------------
# Same URL ke duplicate versions ko remove karne mein help
# karta hai.
def normalize_url(url):
    url, _ = urldefrag(url)

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    domain = parsed.netloc.lower()

    path = parsed.path

    return f"{scheme}://{domain}{path}"


# ---------------------------------------------------------
# Check whether URL belongs to allowed AKGEC domains
# ---------------------------------------------------------
def is_allowed_domain(url):
    domain = urlparse(url).netloc.lower()

    return domain in ALLOWED_DOMAINS


# ---------------------------------------------------------
# Check whether URL is a document/resource
# ---------------------------------------------------------
def get_extension(url):
    path = urlparse(url).path.lower()

    return Path(path).suffix


def is_resource(url):
    extension = get_extension(url)

    return extension in RESOURCE_EXTENSIONS


# ---------------------------------------------------------
# Find resources from one webpage
# ---------------------------------------------------------
def extract_resources(page_url):
    print(f"Scanning: {page_url}")

    try:
        response = requests.get(
            page_url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Error: {error}")
        return []


    # HTML ko parse karne ke liye BeautifulSoup use kar rahe hain.
    soup = BeautifulSoup(response.text, "html.parser")

    resources = []


    # ---------------------------------------------------------
    # Search all links
    # ---------------------------------------------------------
    # <a href="..."> ke andar downloadable resources mil sakte hain.
    for tag in soup.find_all("a", href=True):

        resource_url = urljoin(
            page_url,
            tag["href"]
        )

        resource_url = normalize_url(resource_url)


        # Sirf allowed AKGEC domains.
        if not is_allowed_domain(resource_url):
            continue


        # Sirf required document formats.
        if not is_resource(resource_url):
            continue


        resources.append({
            "url": resource_url,
            "source_page": page_url,
            "file_type": get_extension(resource_url)
        })


    return resources


# ---------------------------------------------------------
# Main discovery process
# ---------------------------------------------------------
all_resources = {}
pages_scanned = 0


for start_url in START_URLS:

    resources = extract_resources(start_url)

    pages_scanned += 1


    for resource in resources:

        url = resource["url"]

        # Dictionary URL ko key bana raha hai.
        # Isse duplicate resource automatically remove ho jayega.
        all_resources[url] = resource

    time.sleep(0.5)


# ---------------------------------------------------------
# Convert dictionary to list
# ---------------------------------------------------------
resource_list = list(all_resources.values())


# ---------------------------------------------------------
# Save discovered resources
# ---------------------------------------------------------
with open(
    OUTPUT_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        {
            "pages_scanned": pages_scanned,
            "total_resources": len(resource_list),
            "resources": resource_list
        },
        file,
        ensure_ascii=False,
        indent=4
    )


# ---------------------------------------------------------
# Final report
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("RESOURCE DISCOVERY COMPLETED")
print("=" * 60)

print("Pages scanned:", pages_scanned)
print("Unique resources:", len(resource_list))
print("Output:", OUTPUT_PATH)

for resource in resource_list[:20]:
    print(
        resource["file_type"],
        "->",
        resource["url"]
    )