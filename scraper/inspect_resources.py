import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# Pages where the visible text was unusually short.
# In pages par actual information PDF/document links mein ho sakti hai.
pages = [
    "https://www.akgec.ac.in/grievance-committee/",
    "https://www.akgec.ac.in/mandatory-disclosure/",
    "https://www.akgec.ac.in/nirf-data-for-ranking-2025/",
    "https://www.akgec.ac.in/placements/placed-students/",
    "https://www.akgec.ac.in/placements/our-recruiters/",
    "https://www.akgec.ac.in/aicte-approval-letters/",
]


# File extensions that we want to identify.
# In resources ko next stage mein download/extract karenge.
resource_extensions = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
)


for page_url in pages:

    print("\n" + "=" * 80)
    print("PAGE:")
    print(page_url)
    print("=" * 80)

    try:

        # Download webpage.
        response = requests.get(
            page_url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 AKGEC-RAG-Research"
            }
        )

        print("Status Code:", response.status_code)

        if response.status_code != 200:
            continue


        # Parse HTML.
        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # Find all links.
        links = soup.find_all(
            "a",
            href=True
        )


        found_resources = set()


        # Check every link for downloadable resources.
        for link in links:

            href = link["href"].strip()

            if not href:
                continue


            # Convert relative URL into absolute URL.
            full_url = urljoin(
                page_url,
                href
            )


            # Check file extension.
            lower_url = full_url.lower()

            if lower_url.endswith(
                resource_extensions
            ):

                found_resources.add(
                    full_url
                )


        # Print discovered resources.
        if found_resources:

            print(
                "\nResources Found:",
                len(found_resources)
            )

            for resource in sorted(
                found_resources
            ):

                print(
                    resource
                )

        else:

            print(
                "\nNo direct document links found."
            )


    except requests.RequestException as error:

        print(
            "Request Error:",
            error
        )