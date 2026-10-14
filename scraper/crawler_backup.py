import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from pathlib import Path
import json
import time
import re

# AKGEC ke official domains ko allow karta hai.
ALLOWED_DOMAINS = {
    "www.akgec.ac.in",
    "akgec.ac.in",
    "admissions.akgec.ac.in"
}

START_URL = "https://www.akgec.ac.in/"

# Abhi testing ke liye maximum 50 pages crawl honge.
MAX_PAGES = 50

# Requests ke beech delay rakhta hai taaki website par unnecessary load na ho.
REQUEST_DELAY = 0.5

# In file types ko HTML pages ki tarah crawl nahi karenge.
IGNORED_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".mp4", ".mp3", ".zip", ".rar", ".doc", ".docx",
    ".xls", ".xlsx", ".ppt", ".pptx"
}

# In document types ko future RAG pipeline ke liye collect karenge.
RESOURCE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
}

# Scraped HTML pages yahan JSON format mein save honge.
PAGE_OUTPUT_DIR = Path("data/pages")
PAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Discovered document URLs yahan save honge.
RESOURCE_OUTPUT = Path("data/resource_urls.json")
RESOURCE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# Website ko request ke source ke baare mein batata hai.
HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}


# URL ko standard format mein convert karta hai aur duplicates reduce karta hai.
def normalize_url(url):
    url, _ = urldefrag(url)
    parsed = urlparse(url)

    domain = parsed.netloc.lower()

    if domain == "akgec.ac.in":
        domain = "www.akgec.ac.in"

    path = parsed.path

    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    return f"https://{domain}{path}"


# Sirf allowed AKGEC domains ko crawl karne deta hai.
def is_allowed_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    # Cloudflare email-protection URLs ko skip karta hai.
    if path.startswith("/cdn-cgi/"):
        return False

    return domain in ALLOWED_DOMAINS


# URL se file extension nikalta hai.
def get_extension(url):
    return Path(urlparse(url).path.lower()).suffix


# Check karta hai ki URL downloadable resource hai ya nahi.
def is_resource(url):
    return get_extension(url) in RESOURCE_EXTENSIONS


# URL se safe JSON filename banata hai.
def create_filename(url):
    path = urlparse(url).path.strip("/")

    if not path:
        return "index.json"

    filename = path.replace("/", "_")
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

    return filename + ".json"


# HTML se unnecessary elements remove karke clean text extract karta hai.
def clean_page_text(soup):
    for tag in soup([
        "script",
        "style",
        "noscript",
        "header",
        "nav",
        "footer"
    ]):
        tag.decompose()

    main_content = soup.find("main")

    if main_content:
        # HTML tables ko readable row-wise text mein convert karta hai.
        for table in main_content.find_all("table"):
            rows = []

            for row in table.find_all("tr"):
                cells = [
                    cell.get_text(" ", strip=True)
                    for cell in row.find_all(["th", "td"])
                ]

                if cells:
                    rows.append(" | ".join(cells))

            # Table ko remove karne se pehle uska structured text preserve karta hai.
            table_text = "\n".join(rows)

            if table_text:
                table.replace_with(
                    soup.new_string("\n" + table_text + "\n")
                )
            else:
                table.decompose()

        text = main_content.get_text(
            separator=" ",
            strip=True
        )
    else:
        text = soup.get_text(
            separator=" ",
            strip=True
        )

    # Multiple spaces ko single space mein convert karta hai.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# Page ke andar HTML links aur downloadable resources find karta hai.
def extract_page_links(page_url, soup):
    html_links = []
    resources = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        if not href:
            continue

        absolute_url = urljoin(page_url, href)
        absolute_url = normalize_url(absolute_url)

        if not is_allowed_domain(absolute_url):
            continue

        # PDF/DOC/XLS jaise resources ko alag list mein rakhta hai.
        if is_resource(absolute_url):
            resources.append({
                "url": absolute_url,
                "source_page": page_url,
                "file_type": get_extension(absolute_url)
            })
            continue

        # Images, videos aur documents ko HTML queue mein add nahi karta.
        if get_extension(absolute_url) in IGNORED_EXTENSIONS:
            continue

        html_links.append(absolute_url)

    return html_links, resources


# Crawler ki current state maintain karta hai.
visited_urls = set()
urls_to_visit = [START_URL]
all_resources = {}


# Website ke pages recursively crawl karta hai.
while urls_to_visit and len(visited_urls) < MAX_PAGES:
    current_url = normalize_url(urls_to_visit.pop(0))

    if current_url in visited_urls:
        continue

    if not is_allowed_domain(current_url):
        continue

    print(f"\n[{len(visited_urls) + 1}/{MAX_PAGES}] {current_url}")

    try:
        response = requests.get(
            current_url,
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

    except requests.RequestException as error:
        print("Request error:", error)
        continue

    visited_urls.add(current_url)

    # HTML ko BeautifulSoup ke through parse karta hai.
    soup = BeautifulSoup(response.text, "html.parser")

    # Page ka title aur clean text extract karta hai.
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = clean_page_text(soup)

    # Scraped page ko JSON file mein save karta hai.
    output_file = PAGE_OUTPUT_DIR / create_filename(current_url)

    page_data = {
        "title": title,
        "url": current_url,
        "text": text
    }

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(
            page_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    print("Text length:", len(text))

    # Page ke HTML links aur downloadable resources find karta hai.
    html_links, resources = extract_page_links(
        current_url,
        soup
    )

    # Same resource multiple pages par mile to duplicate remove karta hai.
    for resource in resources:
        all_resources[resource["url"]] = resource

    # New HTML pages ko crawling queue mein add karta hai.
    for link in html_links:
        if link not in visited_urls and link not in urls_to_visit:
            urls_to_visit.append(link)

    # Website par unnecessary load avoid karta hai.
    time.sleep(REQUEST_DELAY)


# Resource dictionary ko list mein convert karta hai.
resource_list = list(all_resources.values())

# Saare discovered resources ko JSON file mein save karta hai.
with open(RESOURCE_OUTPUT, "w", encoding="utf-8") as file:
    json.dump(
        {
            "total_resources": len(resource_list),
            "resources": resource_list
        },
        file,
        ensure_ascii=False,
        indent=4
    )


# Final crawling report show karta hai.
print("\n" + "=" * 60)
print("CRAWLING + RESOURCE DISCOVERY COMPLETED")
print("=" * 60)
print("HTML pages visited:", len(visited_urls))
print("Unique resources:", len(resource_list))
print("Resource list:", RESOURCE_OUTPUT)

print("\nFirst 20 resources:")

for resource in resource_list[:20]:
    print(
        resource["file_type"],
        "->",
        resource["url"]
    )