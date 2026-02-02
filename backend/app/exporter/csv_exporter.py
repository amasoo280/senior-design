import csv
from typing import List, Dict, Any

def generate_csv(
    rows: List[Dict[str, Any]],
    file_path: str
) -> str:
    if not rows:
        raise ValueError("No data to export")

    fieldnames = rows[0].keys()

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return file_path
