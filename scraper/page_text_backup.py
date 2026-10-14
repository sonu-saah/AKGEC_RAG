import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path


# Test webpage
# Abhi ek AKGEC webpage ka structured data save karenge.
url = "https://www.akgec.ac.in/vision-and-mission/"


# Download webpage
# Requests website ka HTML download karega.
response = requests.get(
    url,
    timeout=10,
    headers={
        "User-Agent": "Mozilla/5.0 AKGEC-RAG-Research"
    }
)


# Check request status
print("Status Code:", response.status_code)


# Convert HTML into searchable structure
# BeautifulSoup HTML ko parse karega.
soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# Remove unnecessary elements
# Header, navigation, footer aur scripts RAG ke main content ka part nahi hain.
for tag in soup([
    "script",
    "style",
    "noscript",
    "header",
    "nav",
    "footer"
]):
    tag.decompose()


# Extract webpage title
# Title ko metadata ke roop mein save karenge.
if soup.title:
    title = soup.title.get_text(
        " ",
        strip=True
    )
else:
    title = "No Title"


# Find main webpage content
# Main tag available ho to usi ko use karenge.
main_content = soup.find("main")


# Fallback
# Agar main tag nahi mila to body use karenge.
if main_content is None:
    main_content = soup.body


# Extract clean text
# HTML tags remove karke readable text nikala jayega.
if main_content:
    text = main_content.get_text(
        separator=" ",
        strip=True
    )
else:
    text = ""


# Clean extra spaces
# Multiple spaces ko single space mein convert karenge.
text = " ".join(text.split())


# Create structured data
# Title, source URL aur clean text ko ek object mein store kar rahe hain.
page_data = {
    "title": title,
    "url": url,
    "text": text
}


# Create output folder
# data/pages folder automatically create ho jayega agar exist nahi karta.
output_folder = Path("data/pages")

output_folder.mkdir(
    parents=True,
    exist_ok=True
)


# Create output filename
# Vision and Mission page ke liye readable filename banayenge.
output_file = output_folder / "vision-and-mission.json"


# Save data as JSON
# UTF-8 encoding Hindi/Unicode text ko bhi safely support karegi.
with open(
    output_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        page_data,
        file,
        ensure_ascii=False,
        indent=4
    )


# Show result
print("\n" + "=" * 60)

print("DATA SAVED SUCCESSFULLY")

print("File:")
print(output_file)

print("\nTitle:")
print(title)

print("\nSource URL:")
print(url)

print("\nText length:")
print(len(text), "characters")

print("=" * 60)