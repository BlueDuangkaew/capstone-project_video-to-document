"""
NLP Processing Package for Video Documentation Pipeline

This package provides a complete pipeline for processing Whisper transcripts
into structured, hierarchical documentation.

Modules:
    - nlp_config: Configuration and settings
    - text_cleaner: Text cleaning and normalization
    - segment_classifier: Segment classification
    - summarizer: Text summarization
    - step_extractor: Step extraction
    - doc_structurer: Document structuring
    - pipeline: Main pipeline orchestration

Example:
    >>> from nlp import process_transcript, export_to_json
    >>> import json
    >>> 
    >>> with open("transcript.json") as f:
    ...     transcript = json.load(f)
    >>> 
    >>> document = process_transcript(transcript, use_llm=False)
    >>> export_to_json(document, "output.json")
"""

from .nlp_config import NLPConfig
from .text_cleaner import TextCleaner
from .segment_classifier import SegmentClassifier
from .summarizer import Summarizer
from .step_extractor import StepExtractor
from .doc_structurer import DocumentStructurer
from .pipeline import (
    process_transcript,
    export_to_json,
    export_to_markdown,
    export_to_html
)

__version__ = "1.0.0"

__all__ = [
    # Configuration
    'NLPConfig',
    
    # Core Modules
    'TextCleaner',
    'SegmentClassifier',
    'Summarizer',
    'StepExtractor',
    'DocumentStructurer',
    
    # Pipeline Functions
    'process_transcript',
    'export_to_json',
    'export_to_markdown',
    'export_to_html',
]
