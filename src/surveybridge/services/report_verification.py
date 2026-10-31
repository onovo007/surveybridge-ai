"""PDF structure verification only. Numeric table extraction is intentionally disabled."""

import io
import re
from datetime import datetime


def inspect_pdf(body):
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(body))
        if reader.is_encrypted or len(reader.pages) > 1500:
            raise ValueError("Encrypted or over-limit report requires manual review")
        front = "\n".join((p.extract_text() or "") for p in reader.pages[:8])
        cover = "\n".join((p.extract_text() or "") for p in reader.pages[:3])
        dates = re.findall(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2}|19\d{2})\b",
            cover,
        )
        cover_date = (
            datetime.strptime(" ".join(dates[-1]), "%B %Y").strftime("%Y-%m") if dates else None
        )
        match = re.search(
            r"[Ff]ieldwork.{0,80}?between\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\s+and\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})",
            " ".join(front.split()),
        )
        fieldwork = None
        if match:
            try:
                fieldwork = {
                    "start": datetime.strptime(match[1], "%d %B %Y").date().isoformat(),
                    "end": datetime.strptime(match[2], "%d %B %Y").date().isoformat(),
                    "method": "literal_fieldwork_sentence_front_matter",
                }
            except ValueError:
                pass
        return {
            "page_count": len(reader.pages),
            "cover_date": cover_date,
            "cover_date_precision": "month" if cover_date else None,
            "official_mini_design_label": bool(
                re.search(r"mini[\s-]*(?:demographic|dhs)", cover, re.I)
            ),
            "fieldwork_sentence": fieldwork,
            "verification_method": "pypdf_front_matter_structure",
            "numeric_estimates_extracted": False,
            "tables": "Complex tables require independent page/table/denominator validation; extraction disabled",
        }
    except Exception as exc:
        raise ValueError(f"PDF structure could not be verified: {type(exc).__name__}") from exc
