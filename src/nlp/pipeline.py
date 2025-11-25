"""
Pipeline Module
Main orchestration for the NLP processing pipeline.
Coordinates all modules and provides export functionality.
"""

import json
import logging
from typing import Dict, Optional, Protocol
from pathlib import Path

from .text_cleaner import TextCleaner
from .segment_classifier import SegmentClassifier
from .summarizer import Summarizer
from .step_extractor import StepExtractor
from .doc_structurer import DocumentStructurer

logger = logging.getLogger(__name__)


class LLMModel(Protocol):
    """Protocol for LLM model wrappers"""
    def generate(self, prompt: str) -> str:
        """Generate text completion from prompt"""
        ...
    
    def generate_list(self, prompt: str) -> list:
        """Generate a list of items from prompt"""
        ...


def process_transcript(
    transcript_json: Dict, 
    model: Optional[LLMModel] = None,
    use_llm: bool = False
) -> Dict:
    """
    Complete NLP processing pipeline
    
    Args:
        transcript_json: Raw Whisper transcript
        model: Optional LLM model wrapper
        use_llm: Whether to use LLM for processing
        
    Returns:
        Structured document dictionary
        
    Example:
        >>> with open("transcript.json") as f:
        ...     transcript = json.load(f)
        >>> document = process_transcript(transcript, use_llm=False)
        >>> print(document['summary'])
    """
    logger.info(f"Processing transcript: {transcript_json.get('segment_id')}")
    
    # Initialize modules
    cleaner = TextCleaner()
    classifier = SegmentClassifier(model=model)
    summarizer = Summarizer(model=model)
    stepper = StepExtractor(model=model)
    structurer = DocumentStructurer()
    
    # Execute pipeline
    try:
        # Step 1: Clean segments
        logger.info("Step 1/5: Cleaning segments...")
        cleaned = cleaner.clean_segments(transcript_json.get("segments", []))
        
        # Step 2: Classify segments
        logger.info("Step 2/5: Classifying segments...")
        classified = classifier.classify_segments(cleaned, use_llm=use_llm)
        
        # Step 3: Generate summary
        logger.info("Step 3/5: Generating summary...")
        summary = summarizer.summarize_segments(classified, use_llm=use_llm)
        
        # Step 4: Extract steps
        logger.info("Step 4/5: Extracting steps...")
        steps = stepper.extract_steps(classified, use_llm=use_llm)
        
        # Step 5: Build document
        logger.info("Step 5/5: Building document structure...")
        document = structurer.build_document(
            transcript_json,
            cleaned,
            classified,
            steps,
            summary
        )
        
        logger.info("Pipeline completed successfully")
        return document
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise


def export_to_json(document: Dict, output_path: str):
    """
    Export document to JSON file
    
    Args:
        document: Structured document dictionary
        output_path: Path where to save the JSON file
        
    Example:
        >>> export_to_json(document, "output/doc.json")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(document, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exported to JSON: {output_path}")


def export_to_markdown(document: Dict, output_path: str):
    """
    Export document to Markdown file
    
    Args:
        document: Structured document dictionary
        output_path: Path where to save the Markdown file
        
    Example:
        >>> export_to_markdown(document, "output/doc.md")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    md_lines = [
        f"# {document['title']}",
        "",
        "## Summary",
        document['summary'],
        "",
    ]
    
    # Add steps if any
    if document.get('steps'):
        md_lines.append("## Steps")
        md_lines.append("")
        for i, step in enumerate(document['steps'], 1):
            md_lines.append(f"{i}. {step}")
        md_lines.append("")
    
    # Add key concepts if any
    if document.get('key_concepts'):
        md_lines.extend(["## Key Concepts", ""])
        for concept in document['key_concepts']:
            md_lines.append(f"- {concept}")
        md_lines.append("")
    
    # Add timeline
    md_lines.extend([
        "## Timeline",
        ""
    ])
    
    for item in document['timeline']:
        md_lines.append(
            f"**{item['start_formatted']} - {item['end_formatted']}** "
            f"[{item['label']}]: {item['text']}"
        )
    
    # Add metadata
    md_lines.extend([
        "",
        "## Metadata",
        "",
        f"- **Video ID**: {document['video_id']}",
        f"- **Language**: {document['metadata'].get('language', 'unknown')}",
        f"- **Model**: {document['metadata'].get('model', 'unknown')}",
        f"- **Duration**: {document['metadata'].get('duration', 'unknown')}s",
        f"- **Processed Segments**: {document['metadata'].get('processed_segments', 0)}",
        "",
    ])
    
    # Add statistics
    if document.get('statistics'):
        stats = document['statistics']
        md_lines.extend([
            "## Statistics",
            "",
            f"- **Total Segments**: {stats.get('total_segments', 0)}",
            f"- **Total Words**: {stats.get('total_words', 0)}",
            f"- **Average Segment Length**: {stats.get('avg_segment_length', 0):.1f} words",
            "",
            "### Label Distribution",
            ""
        ])
        
        for label, count in stats.get('label_distribution', {}).items():
            md_lines.append(f"- **{label}**: {count}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    
    logger.info(f"Exported to Markdown: {output_path}")


def export_to_html(document: Dict, output_path: str):
    """
    Export document to HTML file
    
    Args:
        document: Structured document dictionary
        output_path: Path where to save the HTML file
        
    Example:
        >>> export_to_html(document, "output/doc.html")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document['title']}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }}
        .step {{ margin: 10px 0; padding: 10px; background: #f1f3f5; border-radius: 4px; }}
        .timeline-item {{ margin: 15px 0; padding: 10px; border-left: 3px solid #28a745; }}
        .label {{ 
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .label-action {{ background: #28a745; color: white; }}
        .label-explanation {{ background: #17a2b8; color: white; }}
        .label-question {{ background: #ffc107; color: black; }}
        .label-transition {{ background: #6c757d; color: white; }}
        .label-statement {{ background: #e9ecef; color: black; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>{document['title']}</h1>
    
    <h2>Summary</h2>
    <div class="summary">{document['summary']}</div>
"""
    
    # Add steps
    if document.get('steps'):
        html += "\n    <h2>Steps</h2>\n"
        for i, step in enumerate(document['steps'], 1):
            html += f'    <div class="step">{i}. {step}</div>\n'
    
    # Add timeline
    html += "\n    <h2>Timeline</h2>\n"
    for item in document['timeline']:
        label_class = f"label-{item['label']}"
        html += f"""    <div class="timeline-item">
        <strong>{item['start_formatted']} - {item['end_formatted']}</strong>
        <span class="label {label_class}">{item['label']}</span><br>
        {item['text']}
"""

        # If the timeline item has an associated GIF path (relative to HTML), embed it
        if item.get('gif'):
            html += f"    <div class=\"timeline-gif\">\n        <img src=\"{item['gif']}\" alt=\"step gif\" style=\"max-width:100%;height:auto;display:block;margin-top:8px;\"/>\n    </div>\n"

        # close the timeline item block
        html += """
    </div>\n"""
    
    # Add metadata
    html += f"""
    <h2>Metadata</h2>
    <div class="metadata">
        <strong>Video ID:</strong> {document['video_id']}<br>
        <strong>Language:</strong> {document['metadata'].get('language', 'unknown')}<br>
        <strong>Total Segments:</strong> {document['statistics'].get('total_segments', 0)}<br>
        <strong>Total Words:</strong> {document['statistics'].get('total_words', 0)}
    </div>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"Exported to HTML: {output_path}")
