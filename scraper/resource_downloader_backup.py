import requests
from pathlib import Path
import json
import re
from urllib.parse import urlparse

# Discovered resource URLs ko JSON file se read karta hai.
RESOURCE_FILE = Path("data/resource_urls.json")

# Downloaded files ko is folder mein save karta hai.
OUTPUT_DIR = Path("data/resources")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Website ko request ke source ke baare mein batata hai.
HEADERS = {
    "User-Agent": "AKGEC-RAG-Research-Bot/1.0"
}

# URL se safe filename banata hai.
def create_filename(url):
    filename = Path(urlparse(url).path).name

    if not filename:
        filename = "resource"

    return re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

# JSON file se resource URLs read karta hai.
def load_resources():
    with open(RESOURCE_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["resources"]

# Ek resource download karke local folder mein save karta hai.
def download_resource(resource):
    url = resource["url"]
    filename = create_filename(url)
    output_file = OUTPUT_DIR / filename

    if output_file.exists():
        print("Already exists:", filename)
        return True

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()

        with open(output_file, "wb") as file:
            file.write(response.content)

        print("Downloaded:", filename)
        return True

    except requests.RequestException as error:
        print("Download failed:", url)
        print("Error:", error)
        return False

# Saare discovered resources download karta hai.
def main():
    resources = load_resources()

    print("Total resources:", len(resources))

    success = 0
    failed = 0

    for resource in resources:
        if download_resource(resource):
            success += 1
        else:
            failed += 1

    print("\nDOWNLOAD COMPLETED")
    print("Successful:", success)
    print("Failed:", failed)
    print("Output folder:", OUTPUT_DIR)


if __name__ == "__main__":
    main()