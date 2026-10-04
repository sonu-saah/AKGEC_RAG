from pathlib import Path
import json

# Downloaded resources ka folder define karta hai.
RESOURCE_DIR = Path("data/resources")

# Inventory report yahan save karega.
OUTPUT_FILE = Path("data/resource_inventory.json")

# File extension ke basis par resources count karta hai.
def get_file_type(file):
    extension = file.suffix.lower()

    if extension:
        return extension[1:].upper()

    return "UNKNOWN"

# Downloaded files ka complete inventory banata hai.
def build_inventory():
    files = list(RESOURCE_DIR.rglob("*"))

    inventory = []
    type_counts = {}

    for file in files:
        if not file.is_file():
            continue

        file_type = get_file_type(file)
        size = file.stat().st_size

        type_counts[file_type] = type_counts.get(file_type, 0) + 1

        inventory.append({
            "filename": file.name,
            "path": str(file),
            "type": file_type,
            "size_bytes": size,
            "empty": size == 0
        })

    return inventory, type_counts

# Inventory report ko JSON mein save karta hai.
def main():
    inventory, type_counts = build_inventory()

    report = {
        "total_files": len(inventory),
        "file_types": type_counts,
        "files": inventory
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("RESOURCE INVENTORY COMPLETED")
    print("Total files:", len(inventory))

    print("\nFile types:")
    for file_type, count in sorted(type_counts.items()):
        print(f"{file_type}: {count}")

    empty_files = [
        item["filename"]
        for item in inventory
        if item["empty"]
    ]

    print("\nEmpty files:", len(empty_files))
    print("Report:", OUTPUT_FILE)

# Program ko directly run karta hai.
if __name__ == "__main__":
    main()
    