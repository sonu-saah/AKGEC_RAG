import json
from pathlib import Path


# Folder containing scraped JSON files
# Yahin crawler ne webpages ka structured data save kiya hai.
data_folder = Path("data/pages")


# Find all JSON files
# Folder ke andar saved saari JSON files ko read karenge.
json_files = list(
    data_folder.glob("*.json")
)


print("=" * 60)

print("SCRAPED DATA QUALITY CHECK")

print("=" * 60)

print(
    "Total JSON files:",
    len(json_files)
)


# Check every JSON file
# Har webpage ka title, URL aur text length verify karenge.
for json_file in sorted(json_files):

    try:

        # Open JSON file
        # UTF-8 encoding Unicode text ko correctly read karegi.
        with open(
            json_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)


        # Read metadata
        title = data.get(
            "title",
            ""
        )

        url = data.get(
            "url",
            ""
        )

        text = data.get(
            "text",
            ""
        )


        # Calculate text length
        text_length = len(text)


        # Show basic information
        print("\nFILE:", json_file.name)

        print("TITLE:", title)

        print("TEXT LENGTH:", text_length)


        # Flag very short pages
        # 200 characters se kam text ko manually inspect karenge.
        if text_length < 200:

            print("⚠️ REVIEW NEEDED: Very short content")


        # Check required metadata
        # RAG ke liye title, URL aur text important hain.
        if not title:

            print("⚠️ Missing title")


        if not url:

            print("⚠️ Missing source URL")


        if not text:

            print("❌ Missing page text")


    except (
        json.JSONDecodeError,
        OSError
    ) as error:

        # Report corrupted/unreadable JSON files
        print(
            "\n❌ ERROR:",
            json_file.name
        )

        print(error)


print("\n" + "=" * 60)

print("QUALITY CHECK COMPLETED")

print("=" * 60)