"""DEPRECATION: moved to examples/run_nlp_pipeline.py

This module used to live at the repo root. To keep the project root clean
example scripts have been moved under the `examples/` directory. Run the
example with:

    python examples/run_nlp_pipeline.py

"""

from pathlib import Path

if __name__ == "__main__":
    print("This script has moved to examples/run_nlp_pipeline.py; run that instead")

import json
import logging
from pathlib import Path

# Import pipeline components
from src.nlp.text_cleaner import TextCleaner
from src.nlp.segment_classifier import SegmentClassifier
from src.nlp.summarizer import Summarizer
from src.nlp.step_extractor import StepExtractor
from src.nlp.doc_structurer import DocumentStructurer
from src.nlp.pipeline import process_transcript, export_to_json, export_to_markdown

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Example 1: Basic Usage (Without LLM)
# ============================================================================

def example_basic_processing():
    """Process a transcript using only rule-based methods"""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Processing (No LLM)")
    print("="*70 + "\n")
    
    # Load transcript from file
    transcript_path = "data/output/transcripts/testseg.json"
    
    # Sample transcript data (replace with actual file loading)
    transcript = {
        "segment_id": "testseg",
        "video_path": "data/input_videos/sample_video.mp4",
        "model": "tiny",
        "duration": 120.5,
        "language": "en",
        "raw_text": "Alright, so I'm gonna try something new...",
        "segments": [
            {
                "start": "0:00:00",
                "end": "0:00:03",
                "text": "Alright, so I'm gonna try something new. I'm gonna try to be like really fast",
                "confidence": -0.31
            },
            {
                "start": "0:00:03",
                "end": "0:00:06",
                "text": "But still tell you everything that I think you need to know",
                "confidence": -0.31
            },
            {
                "start": "0:00:06",
                "end": "0:00:11",
                "text": "So a class in programming can be described as like an object in the real world",
                "confidence": -0.31
            },
            {
                "start": "0:00:11",
                "end": "0:00:15",
                "text": "Click on the file menu and select new project",
                "confidence": -0.25
            },
            {
                "start": "0:00:15",
                "end": "0:00:18",
                "text": "Next, you need to open the settings panel",
                "confidence": -0.22
            }
        ]
    }
    
    # Process without LLM
    document = process_transcript(transcript, use_llm=False)
    
    # Display results
    print(f"Video ID: {document['video_id']}")
    print(f"Title: {document['title']}")
    print(f"\nSummary:\n{document['summary']}")
    print(f"\nSteps ({len(document['steps'])}):")
    for i, step in enumerate(document['steps'], 1):
        print(f"  {i}. {step}")
    
    print(f"\nStatistics:")
    print(f"  Total segments: {document['statistics']['total_segments']}")
    print(f"  Total words: {document['statistics']['total_words']}")
    print(f"  Label distribution: {document['statistics']['label_distribution']}")
    
    # Export results
    output_dir = Path("data/output/documents")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_to_json(document, str(output_dir / "testseg_basic.json"))
    export_to_markdown(document, str(output_dir / "testseg_basic.md"))
    
    print(f"\n✓ Exported to: {output_dir}")
    
    return document


# ============================================================================
# Example 2: With OpenAI LLM Integration
# ============================================================================

def example_with_openai():
    """Process transcript using OpenAI for enhanced results"""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: Processing with OpenAI")
    print("="*70 + "\n")
    
    # OpenAI wrapper class
    class OpenAIModel:
        def __init__(self, api_key: str, model: str = "gpt-4"):
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        
        def generate(self, prompt: str) -> str:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        
        def generate_list(self, prompt: str) -> list:
            response = self.generate(prompt)
            # Parse response into list
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            return lines
    
    # Initialize model (use environment variable for API key)
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("⚠ OPENAI_API_KEY not found in environment variables")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
        return None
    
    model = OpenAIModel(api_key=api_key, model="gpt-4")
    
    # Load transcript
    with open("data/output/transcripts/testseg.json") as f:
        transcript = json.load(f)
    
    # Process with LLM
    document = process_transcript(transcript, model=model, use_llm=True)
    
    # Display results
    print(f"Title: {document['title']}")
    print(f"\nAI-Generated Summary:\n{document['summary']}")
    print(f"\nExtracted Steps ({len(document['steps'])}):")
    for i, step in enumerate(document['steps'], 1):
        print(f"  {i}. {step}")
    
    # Export
    output_dir = Path("data/output/documents")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    export_to_json(document, str(output_dir / "testseg_llm.json"))
    export_to_markdown(document, str(output_dir / "testseg_llm.md"))
    
    print(f"\n✓ Exported to: {output_dir}")
    
    return document


# ============================================================================
# Example 3: Custom Configuration
# ============================================================================

def example_custom_config():
    """Process with custom configuration"""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: Custom Configuration")
    print("="*70 + "\n")
    
    # Custom filler words
    custom_fillers = [
        "um", "uh", "like", "you know",
        "sort of", "kind of", "actually",
        # Add domain-specific fillers
        "okay so", "alright", "right so"
    ]
    
    # Custom classification rules
    custom_rules = {
        "action": ["click", "press", "select", "open", "close", "drag", "type"],
        "navigation": ["go to", "navigate to", "switch to", "move to"],
        "explanation": ["this is", "what happens", "because", "the reason"],
        "warning": ["warning", "careful", "make sure", "don't forget"],
        "tip": ["tip", "pro tip", "remember", "note that"]
    }
    
    # Initialize with custom config
    cleaner = TextCleaner(filler_words=custom_fillers)
    classifier = SegmentClassifier(rules=custom_rules)
    summarizer = Summarizer()
    stepper = StepExtractor()
    structurer = DocumentStructurer()
    
    # Sample transcript
    transcript = {
        "segment_id": "custom_config_test",
        "segments": [
            {"start": "0:00:00", "end": "0:00:03", 
             "text": "Okay so click on the settings icon", "confidence": -0.3},
            {"start": "0:00:03", "end": "0:00:06",
             "text": "Warning: make sure to save your work first", "confidence": -0.25},
            {"start": "0:00:06", "end": "0:00:09",
             "text": "Pro tip: you can use keyboard shortcuts", "confidence": -0.28}
        ]
    }
    
    # Process with custom pipeline
    cleaned = cleaner.clean_segments(transcript["segments"])
    classified = classifier.classify_segments(cleaned)
    summary = summarizer.summarize_segments(classified, use_llm=False)
    steps = stepper.extract_steps(classified)
    document = structurer.build_document(transcript, cleaned, classified, steps, summary)
    
    # Display custom labels
    print("Segments with custom labels:")
    for item in document['timeline']:
        print(f"  [{item['label']}] {item['text']}")
    
    return document


# ============================================================================
# Example 4: Batch Processing
# ============================================================================

def example_batch_processing():
    """Process multiple transcripts in batch"""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch Processing")
    print("="*70 + "\n")
    
    transcript_dir = Path("data/output/transcripts")
    output_dir = Path("data/output/documents")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all transcript files
    transcript_files = list(transcript_dir.glob("*.json"))
    
    if not transcript_files:
        print("⚠ No transcript files found in", transcript_dir)
        return []
    
    print(f"Found {len(transcript_files)} transcript files")
    
    results = []
    
    for transcript_file in transcript_files:
        try:
            print(f"\nProcessing: {transcript_file.name}")
            
            # Load transcript
            with open(transcript_file) as f:
                transcript = json.load(f)
            
            # Process
            document = process_transcript(transcript, use_llm=False)
            
            # Export
            output_name = transcript_file.stem
            export_to_json(document, str(output_dir / f"{output_name}_doc.json"))
            export_to_markdown(document, str(output_dir / f"{output_name}_doc.md"))
            
            results.append(document)
            print(f"  ✓ Processed: {document['video_id']}")
            print(f"    Steps extracted: {len(document['steps'])}")
            
        except Exception as e:
            print(f"  ✗ Error processing {transcript_file.name}: {e}")
            continue
    
    print(f"\n✓ Successfully processed {len(results)} transcripts")
    print(f"✓ Output saved to: {output_dir}")
    
    return results


# ============================================================================
# Example 5: Individual Module Usage
# ============================================================================

def example_individual_modules():
    """Demonstrate using individual modules separately"""
    
    print("\n" + "="*70)
    print("EXAMPLE 5: Individual Module Usage")
    print("="*70 + "\n")
    
    # Sample text
    raw_text = "um so basically you need to like click on the button and uh select the option"
    
    # 1. Text Cleaning
    print("1. Text Cleaning:")
    cleaner = TextCleaner()
    cleaned = cleaner.clean_text(raw_text)
    print(f"   Raw: {raw_text}")
    print(f"   Cleaned: {cleaned}")
    
    # 2. Classification
    print("\n2. Segment Classification:")
    classifier = SegmentClassifier()
    label = classifier.classify(cleaned)
    print(f"   Text: {cleaned}")
    print(f"   Label: {label}")
    
    # 3. Summarization
    print("\n3. Text Summarization:")
    summarizer = Summarizer()
    passages = [
        "First, open the application.",
        "Then, click on the settings menu.",
        "Finally, adjust your preferences."
    ]
    summary = summarizer.summarize_text(passages, use_llm=False)
    print(f"   Summary: {summary}")
    
    # 4. Step Extraction
    print("\n4. Step Extraction:")
    stepper = StepExtractor()
    segments = [
        {"text": "Click the start button.", "label": "action"},
        {"text": "This is important to remember.", "label": "explanation"},
        {"text": "Open the file menu.", "label": "action"}
    ]
    steps = stepper.extract_steps(segments)
    print(f"   Steps extracted: {len(steps)}")
    for i, step in enumerate(steps, 1):
        print(f"     {i}. {step}")


# ============================================================================
# Main execution
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("NLP PIPELINE EXAMPLES")
    print("="*70)
    
    # Run examples
    try:
        # Example 1: Basic processing
        doc1 = example_basic_processing()
        
        # Example 2: OpenAI (uncomment if you have API key)
        # doc2 = example_with_openai()
        
        # Example 3: Custom config
        doc3 = example_custom_config()
        
        # Example 4: Batch processing (uncomment if you have multiple files)
        # docs = example_batch_processing()
        
        # Example 5: Individual modules
        example_individual_modules()
        
        print("\n" + "="*70)
        print("✓ All examples completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


# ============================================================================
# Utility functions for specific use cases
# ============================================================================

def process_single_file(input_path: str, output_path: str, use_llm: bool = False):
    """
    Convenience function to process a single transcript file
    
    Args:
        input_path: Path to input transcript JSON
        output_path: Path for output document JSON
        use_llm: Whether to use LLM processing
    """
    with open(input_path) as f:
        transcript = json.load(f)
    
    document = process_transcript(transcript, use_llm=use_llm)
    
    export_to_json(document, output_path)
    export_to_markdown(output_path.replace('.json', '.md'), document)
    
    return document


def get_processing_stats(documents: list) -> dict:
    """
    Get aggregate statistics from multiple processed documents
    
    Args:
        documents: List of processed document dicts
        
    Returns:
        Aggregate statistics
    """
    total_segments = sum(d['statistics']['total_segments'] for d in documents)
    total_words = sum(d['statistics']['total_words'] for d in documents)
    total_steps = sum(len(d['steps']) for d in documents)
    
    return {
        "total_documents": len(documents),
        "total_segments": total_segments,
        "total_words": total_words,
        "total_steps": total_steps,
        "avg_segments_per_doc": total_segments / len(documents) if documents else 0,
        "avg_steps_per_doc": total_steps / len(documents) if documents else 0
    }
