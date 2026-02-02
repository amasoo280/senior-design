import os
from datetime import datetime
from typing import List, Dict, Any

from app.exporter.csv_exporter import generate_csv
from app.exporter.pdf_exporter import generate_pdf

EXPORT_DIR = "exports"

def export_results(
    rows: List[Dict[str, Any]],
    request_id: str,
    format_type: str = "both"
) -> dict:
    """
    Export query results to CSV and/or PDF.
    
    Args:
        rows: List of result dictionaries
        request_id: Unique request identifier
        format_type: "csv", "pdf", or "both"
        
    Returns:
        Dictionary with paths to generated files
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base_name = f"query_{request_id}_{timestamp}"

    result = {}

    if format_type in ("csv", "both"):
        csv_path = os.path.join(EXPORT_DIR, f"{base_name}.csv")
        generate_csv(rows, csv_path)
        result["csv"] = csv_path

    if format_type in ("pdf", "both"):
        pdf_path = os.path.join(EXPORT_DIR, f"{base_name}.pdf")
        generate_pdf(rows, pdf_path)
        result["pdf"] = pdf_path

    return result
