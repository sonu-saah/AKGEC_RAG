import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "akgec_master_v13.json"
OUTPUT = ROOT / "data" / "akgec_rag_chunks_v2.json"

MAX_CHARS = 1100
OVERLAP = 120


# Split long text without changing its content.
def split_text(text):
    text = str(text).strip()

    if len(text) <= MAX_CHARS:
        return [text] if text else []

    parts = []
    start = 0

    while start < len(text):
        end = min(start + MAX_CHARS, len(text))

        if end < len(text):
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind(" ", start, end)
            )

            if boundary > start + MAX_CHARS // 2:
                end = boundary + 1

        part = text[start:end].strip()

        if part:
            parts.append(part)

        if end == len(text):
            break

        start = max(start + 1, end - OVERLAP)

    return parts


# Convert a table row into searchable text.
def format_table_row(row, header=None):
    cells = [str(cell).strip() for cell in row]

    if header and len(header) == len(cells):
        return " | ".join(
            f"{key}: {value}"
            for key, value in zip(header, cells)
            if value
        )

    if len(cells) >= 4 and len(cells) % 2 == 0:
        pairs = []

        for index in range(0, len(cells), 2):
            key = cells[index]
            value = cells[index + 1]

            if key and value:
                pairs.append(f"{key}: {value}")

        if pairs:
            return " | ".join(pairs)

    return " | ".join(cell for cell in cells if cell)


# Generate searchable chunks from master JSON blocks.
def main():
    master = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    chunks = []

    for section_index, section in enumerate(master):
        title = str(section.get("title", "")).strip()
        source_url = str(section.get("source_url", "")).strip()
        current_heading = ""

        for block_index, block in enumerate(section.get("blocks", [])):
            kind = block.get("type", "")

            if kind == "heading":
                current_heading = str(block.get("text", "")).strip()
                continue

            texts = []

            if kind in ("paragraph", "list_item", "link", "document"):
                content = str(block.get("text", "")).strip()

                if content:
                    texts.append((content, None))

            elif kind == "table":
                rows = block.get("rows", [])
                header = None

                if rows and all(
                    isinstance(cell, str) for cell in rows[0]
                ):
                    first = [cell.lower().strip() for cell in rows[0]]

                    if any(
                        term in cell
                        for cell in first
                        for term in ("s.no", "name of", "status", "year")
                    ):
                        header = rows[0]
                        rows = rows[1:]

                for row in rows:
                    if not isinstance(row, list):
                        continue

                    formatted = format_table_row(row, header)

                    if formatted:
                        texts.append((
                            formatted,
                            block.get("source_page")
                        ))

            for item_index, (content, source_page) in enumerate(texts):
                for part_index, part in enumerate(split_text(content)):
                    prefix = f"Section: {title}\n"

                    if current_heading:
                        prefix += f"Heading: {current_heading}\n"

                    text = prefix + part

                    chunk_id = (
                        f"v2_{section_index}_"
                        f"{block_index}_{item_index}_{part_index}"
                    )

                    chunks.append({
                        "id": chunk_id,
                        "text": text,
                        "title": title,
                        "section": title,
                        "source_url": source_url,
                        "content_type": kind,
                        "source_page": source_page,
                        "block_index": block_index,
                        "chunk_index": part_index,
                        "verification_status": "master_source"
                    })

    ids = [chunk["id"] for chunk in chunks]

    assert len(ids) == len(set(ids)), "Duplicate chunk IDs"

    OUTPUT.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("V2 CHUNK GENERATION COMPLETE")
    print("Sections:", len(master))
    print("Chunks:", len(chunks))
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
