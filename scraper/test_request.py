import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


# Starting website URL
# Crawler yahin se start hoga.
base_url = "https://www.akgec.ac.in/"


# Send request to the website
# Website ka HTML download kar rahe hain.
response = requests.get(base_url)


# Convert HTML into searchable structure
# BeautifulSoup HTML ke elements ko search karne mein help karta hai.
soup = BeautifulSoup(response.text, "html.parser")


# Store unique AKGEC URLs
# set() duplicate URLs ko automatically remove karega.
internal_urls = set()


# Find all links from homepage
# Har <a> tag ka href URL nikalenge.
for link in soup.find_all("a", href=True):

    # Get URL from href
    href = link["href"]

    # Convert relative URL into complete URL
    # Example: /courses/ → https://www.akgec.ac.in/courses/
    full_url = urljoin(base_url, href)

    # Get domain information
    parsed_url = urlparse(full_url)

    # Keep only main AKGEC domain
    if parsed_url.netloc == "www.akgec.ac.in":
        internal_urls.add(full_url)


# Classify each URL
# URL extension dekhkar PDF, image ya webpage identify karenge.
print("\nURL Types:\n")


for url in sorted(internal_urls):

    # Convert URL into lowercase
    # Isse .PDF aur .pdf dono easily identify ho jayenge.
    lower_url = url.lower()

    # Check PDF
    if lower_url.endswith(".pdf"):
        url_type = "PDF"

    # Check common image formats
    elif lower_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
        url_type = "IMAGE"

    # Otherwise treat it as a webpage
    else:
        url_type = "WEBPAGE"

    print(url_type, "→", url)