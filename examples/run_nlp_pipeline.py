"""
Example usage script for the NLP pipeline (moved into examples/ for tidiness).

This is a convenience script demonstrating pipeline usage.
"""

import json
import logging
from pathlib import Path

from src.nlp.pipeline import process_transcript, export_to_json, export_to_markdown

logging.basicConfig(level=logging.INFO)

def main():
    sample = Path("data/output/transcripts/testseg.json")
    if not sample.exists():
        print("Sample transcript not found:", sample)
        return

    with open(sample, "r", encoding="utf-8") as fh:
        transcript = json.load(fh)

    doc = process_transcript(transcript, use_llm=False)

    out_dir = Path("data/output/documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    export_to_json(doc, str(out_dir / "example_doc.json"))
    export_to_markdown(doc, str(out_dir / "example_doc.md"))

    print("Exported example documents to:", out_dir)


if __name__ == "__main__":
    main()
