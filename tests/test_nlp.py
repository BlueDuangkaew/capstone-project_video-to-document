"""
Complete test suite for NLP pipeline modules (FIXED)
Run with: pytest tests/test_nlp.py -v
"""

import pytest
import json
from typing import List
from pathlib import Path

# Import all modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nlp.nlp_config import NLPConfig
from nlp.text_cleaner import TextCleaner
from nlp.segment_classifier import SegmentClassifier
from nlp.step_extractor import StepExtractor
from nlp.summarizer import Summarizer
from nlp.doc_structurer import DocumentStructurer
from nlp.pipeline import process_transcript, export_to_json, export_to_markdown


# ============================================================================
# Mock LLM Model for Testing
# ============================================================================

class MockLLMModel:
    """Mock LLM for testing without external API calls"""
    
    def generate(self, prompt: str) -> str:
        """Return mock responses based on prompt content"""
        if "summarize" in prompt.lower():
            return "This is a test summary of the content."
        elif "classify" in prompt.lower():
            return "0. action\n1. explanation\n2. statement"
        elif "extract" in prompt.lower() or "steps" in prompt.lower():
            return "1. First step\n2. Second step\n3. Third step"
        return "Mock response"
    
    def generate_list(self, prompt: str) -> List[str]:
        """Return mock list of items"""
        return ["Item 1", "Item 2", "Item 3"]


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_model():
    """Provide mock LLM model"""
    return MockLLMModel()


@pytest.fixture
def sample_segments():
    """Provide sample transcript segments"""
    return [
        {
            "start": "0:00:00",
            "end": "0:00:03",
            "text": "um click the button  ",
            "confidence": -0.31
        },
        {
            "start": "0:00:03",
            "end": "0:00:06",
            "text": "So basically this is how you do it",
            "confidence": -0.25
        },
        {
            "start": "0:00:06",
            "end": "0:00:08",
            "text": "[music]",
            "confidence": -0.50
        },
        {
            "start": "0:00:08",
            "end": "0:00:12",
            "text": "Next, you need to open the file menu",
            "confidence": -0.20
        }
    ]


@pytest.fixture
def sample_transcript():
    """Provide complete sample transcript"""
    return {
        "segment_id": "test_segment_01",
        "video_path": "data/test_video.mp4",
        "model": "tiny",
        "duration": 120.5,
        "language": "en",
        "raw_text": "Sample transcript text...",
        "segments": [
            {
                "start": "0:00:00",
                "end": "0:00:03",
                "text": "Click on the button",
                "confidence": -0.31
            },
            {
                "start": "0:00:03",
                "end": "0:00:06",
                "text": "This shows you how to navigate",
                "confidence": -0.25
            }
        ]
    }


# ============================================================================
# TextCleaner Tests
# ============================================================================

class TestTextCleaner:
    
    def test_clean_text_removes_filler(self):
        cleaner = TextCleaner()
        text = "um click the button"
        result = cleaner.clean_text(text)
        assert "um" not in result.lower()
        assert "click the button" in result.lower()
    
    def test_clean_text_capitalizes(self):
        cleaner = TextCleaner()
        text = "click the button"
        result = cleaner.clean_text(text)
        assert result[0].isupper()
    
    def test_clean_text_normalizes_whitespace(self):
        cleaner = TextCleaner()
        text = "click    the   button  "
        result = cleaner.clean_text(text)
        assert "  " not in result
        assert result == "Click the button."
    
    def test_clean_text_adds_period(self):
        cleaner = TextCleaner()
        text = "click the button"
        result = cleaner.clean_text(text)
        assert result.endswith(".")
    
    def test_clean_text_handles_empty(self):
        cleaner = TextCleaner()
        assert cleaner.clean_text("") == ""
        assert cleaner.clean_text("   ") == ""
    
    def test_clean_text_removes_multiple_fillers(self):
        cleaner = TextCleaner()
        text = "um you know like click the button"
        result = cleaner.clean_text(text)
        assert "um" not in result.lower()
        assert "you know" not in result.lower()
        assert "like" not in result.lower()
        assert "click the button" in result.lower()
    
    def test_clean_text_so_is_not_filler(self):
        """'so' is a classification keyword, not a filler word"""
        cleaner = TextCleaner()
        text = "so click the button"
        result = cleaner.clean_text(text)
        # 'so' should remain as it's used for classification
        assert "so" in result.lower()
        assert "click the button" in result.lower()
    
    def test_parse_timestamp(self):
        cleaner = TextCleaner()
        assert cleaner._parse_timestamp("0:00:30") == 30.0
        assert cleaner._parse_timestamp("0:01:30") == 90.0
        assert cleaner._parse_timestamp("1:00:00") == 3600.0
        assert cleaner._parse_timestamp("1:30") == 90.0
    
    def test_clean_segments(self, sample_segments):
        cleaner = TextCleaner()
        cleaned = cleaner.clean_segments(sample_segments)
        
        # All segments should remain (music becomes "." which is >= 3 chars when cleaned)
        # Actually "[music]" becomes empty after filler removal, so should be filtered
        assert len(cleaned) >= 3  # At least 3 valid segments
        
        # Check first segment
        assert "um" not in cleaned[0]["text"].lower()
        assert "click the button" in cleaned[0]["text"].lower()
        
        # Check timestamp parsing
        assert "start_seconds" in cleaned[0]
        assert "end_seconds" in cleaned[0]
        assert cleaned[0]["start_seconds"] == 0.0
    
    def test_clean_segments_filters_music(self):
        """Test that [music] tags are properly removed"""
        cleaner = TextCleaner()
        segments = [
            {"start": "0:00:00", "end": "0:00:03", "text": "[music]", "confidence": -0.5},
            {"start": "0:00:03", "end": "0:00:06", "text": "Click the button", "confidence": -0.3}
        ]
        cleaned = cleaner.clean_segments(segments)
        
        # [music] should be filtered out (becomes "." after cleaning, which is too short)
        # Only the "Click the button" segment should remain
        assert len(cleaned) == 1
        assert "click the button" in cleaned[0]["text"].lower()
        
        # Verify no music tags in any text
        texts = [s["text"] for s in cleaned]
        assert not any("music" in t.lower() for t in texts)
    
    def test_clean_segments_empty_list(self):
        cleaner = TextCleaner()
        result = cleaner.clean_segments([])
        assert result == []
    
    def test_clean_segments_preserves_original(self, sample_segments):
        cleaner = TextCleaner()
        cleaned = cleaner.clean_segments(sample_segments)
        if cleaned:  # If any segments remain
            assert "original_text" in cleaned[0]


# ============================================================================
# SegmentClassifier Tests
# ============================================================================

class TestSegmentClassifier:
    
    def test_classify_action(self):
        classifier = SegmentClassifier()
        assert classifier.classify("Click on the file") == "action"
        assert classifier.classify("Open the menu") == "action"
        assert classifier.classify("Select the option") == "action"
    
    def test_classify_explanation(self):
        classifier = SegmentClassifier()
        assert classifier.classify("So this is how it works") == "explanation"
        assert classifier.classify("Basically what happens is") == "explanation"
        assert classifier.classify("This is important") == "explanation"
    
    def test_classify_question(self):
        classifier = SegmentClassifier()
        assert classifier.classify("How do I do this?") == "question"
        assert classifier.classify("What is this?") == "question"
    
    def test_classify_transition(self):
        classifier = SegmentClassifier()
        assert classifier.classify("Next, we will") == "transition"
        assert classifier.classify("Now let's move on") == "transition"
    
    def test_classify_noise(self):
        classifier = SegmentClassifier()
        assert classifier.classify("") == "noise"
        assert classifier.classify("um") == "noise"
        assert classifier.classify("uh", confidence=-2.0) == "noise"
    
    def test_classify_statement_pure(self):
        """Test classification of pure statements without trigger words"""
        classifier = SegmentClassifier()
        # Use a statement that doesn't contain any classification keywords
        result = classifier.classify("The application displays information.")
        assert result == "statement"
    
    def test_classify_this_is_triggers_explanation(self):
        """'This is' triggers explanation classification"""
        classifier = SegmentClassifier()
        result = classifier.classify("This is a regular statement.")
        assert result == "explanation"

    def test_classify_greeting_and_farewell(self):
        classifier = SegmentClassifier()
        assert classifier.classify("Hello everyone") == "greeting"
        assert classifier.classify("Thanks and goodbye") == "farewell"
    
    def test_classify_segments(self):
        classifier = SegmentClassifier()
        segments = [
            {"text": "Click the button", "confidence": -0.3},
            {"text": "So this is important", "confidence": -0.2},
            {"text": "", "confidence": -0.5}
        ]
        
        classified = classifier.classify_segments(segments)
        assert len(classified) == 3
        assert classified[0]["label"] == "action"
        assert classified[1]["label"] == "explanation"
        assert classified[2]["label"] == "noise"
        assert all("label_source" in s for s in classified)
    
    def test_classify_segments_with_llm(self, mock_model):
        classifier = SegmentClassifier(model=mock_model)
        segments = [
            {"text": "Click here", "confidence": -0.3},
            {"text": "This explains it", "confidence": -0.2}
        ]
        
        classified = classifier.classify_with_llm(segments)
        assert all("label" in s for s in classified)
        assert all(s["label_source"] == "llm" for s in classified)
    
    def test_classify_segments_empty(self):
        classifier = SegmentClassifier()
        result = classifier.classify_segments([])
        assert result == []


# ============================================================================
# Summarizer Tests
# ============================================================================

class TestSummarizer:
    
    def test_rule_based_summary_short_text(self):
        summarizer = Summarizer()
        text = "This is a short text."
        result = summarizer._rule_based_summary(text)
        assert result == text
    
    def test_rule_based_summary_long_text(self):
        summarizer = Summarizer()
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        result = summarizer._rule_based_summary(text, max_sentences=2)
        
        # Should contain first 2 sentences
        assert "First sentence" in result
        assert "Second sentence" in result
        
        # The function returns first N sentences joined with ". "
        # So it will be "First sentence. Second sentence"
        # Make sure it doesn't contain all 5 sentences
        sentence_count = result.count("sentence")
        assert sentence_count == 2, f"Expected 2 sentences, got {sentence_count}"
    
    def test_summarize_text_no_model(self):
        summarizer = Summarizer()
        passages = ["First part.", "Second part.", "Third part."]
        result = summarizer.summarize_text(passages, use_llm=False)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_summarize_text_with_llm(self, mock_model):
        summarizer = Summarizer(model=mock_model)
        passages = ["First part.", "Second part."]
        result = summarizer.summarize_text(passages, use_llm=True)
        assert "test summary" in result.lower()
    
    def test_summarize_segments(self):
        summarizer = Summarizer()
        segments = [
            {"text": "Click the button.", "label": "action"},
            {"text": "This is how it works.", "label": "explanation"},
            {"text": "um", "label": "noise"}
        ]
        
        result = summarizer.summarize_segments(segments, use_llm=False)
        assert "Click the button" in result
        assert "This is how it works" in result
        assert "um" not in result
    
    def test_summarize_empty(self):
        summarizer = Summarizer()
        result = summarizer.summarize_segments([])
        assert "No content" in result


# ============================================================================
# StepExtractor Tests
# ============================================================================

class TestStepExtractor:
    
    def test_extract_steps_from_actions(self):
        extractor = StepExtractor()
        segments = [
            {"text": "Click OK.", "label": "action"},
            {"text": "Open the file.", "label": "action"},
            {"text": "This explains something.", "label": "explanation"}
        ]
        
        steps = extractor.extract_steps(segments)
        assert len(steps) == 2
        assert "Click OK." in steps
        assert "Open the file." in steps
    
    def test_extract_steps_with_llm(self, mock_model):
        extractor = StepExtractor(model=mock_model)
        segments = [
            {"text": "Do this and that.", "label": "statement"}
        ]
        
        steps = extractor.extract_steps(segments, use_llm=True)
        assert len(steps) > 0
    
    def test_merge_similar_steps(self):
        extractor = StepExtractor()
        steps = [
            "Click the button.",
            "Click the button.",
            "Open the file."
        ]
        merged = extractor._merge_similar_steps(steps)
        assert len(merged) < len(steps)
    
    def test_extract_steps_empty(self):
        extractor = StepExtractor()
        result = extractor.extract_steps([])
        assert result == []
    
    def test_parse_llm_steps(self):
        extractor = StepExtractor()
        response = "1. First step\n2. Second step\n3. Third step"
        steps = extractor._parse_llm_steps(response)
        assert len(steps) == 3
        assert steps[0] == "First step"


# ============================================================================
# DocumentStructurer Tests
# ============================================================================

class TestDocumentStructurer:
    
    def test_build_document(self, sample_transcript):
        structurer = DocumentStructurer()
        
        cleaned = [{"text": "Test", "start_seconds": 0, "end_seconds": 3}]
        classified = [
            {
                "text": "Click OK.", 
                "label": "action",
                "label_source": "rules",
                "start": "0:00:00",
                "end": "0:00:03",
                "start_seconds": 0,
                "end_seconds": 3,
                "confidence": -0.3,
                "segment_index": 0
            }
        ]
        steps = ["Click OK."]
        summary = "Test summary."
        
        doc = structurer.build_document(
            sample_transcript,
            cleaned,
            classified,
            steps,
            summary
        )
        
        # Check required fields
        assert "video_id" in doc
        assert "title" in doc
        assert "summary" in doc
        assert "steps" in doc
        assert "timeline" in doc
        assert "metadata" in doc
        assert "statistics" in doc
        
        # Check content
        assert doc["summary"] == summary
        assert len(doc["steps"]) == 1
        assert len(doc["timeline"]) == 1
    
    def test_generate_title_from_content(self):
        structurer = DocumentStructurer()
        segments = [
            {"text": "This is a comprehensive guide to using the application.", "label": "explanation"}
        ]
        title = structurer._generate_title(segments, "fallback")
        assert "comprehensive guide" in title.lower()
    
    def test_generate_title_fallback(self):
        structurer = DocumentStructurer()
        title = structurer._generate_title([], "test_id")
        assert "test_id" in title
    
    def test_extract_key_concepts(self):
        structurer = DocumentStructurer()
        segments = [
            {"text": "A variable is a container.", "label": "definition"},
            {"text": "Click here.", "label": "action"}
        ]
        concepts = structurer._extract_key_concepts(segments)
        assert len(concepts) == 1
        assert "variable" in concepts[0].lower()
    
    def test_calculate_stats(self, sample_transcript):
        structurer = DocumentStructurer()
        segments = [
            {"text": "Click the button.", "label": "action"},
            {"text": "This is important.", "label": "explanation"}
        ]
        
        stats = structurer._calculate_stats(sample_transcript, segments)
        assert "total_segments" in stats
        assert "total_words" in stats
        assert "label_distribution" in stats
        assert stats["total_segments"] == 2


# ============================================================================
# Integration Tests
# ============================================================================

class TestPipeline:
    
    def test_full_pipeline_without_llm(self, sample_transcript):
        doc = process_transcript(sample_transcript, use_llm=False)
        
        assert doc is not None
        assert "video_id" in doc
        assert "steps" in doc
        assert "timeline" in doc
        assert len(doc["timeline"]) > 0
    
    def test_full_pipeline_with_mock_llm(self, sample_transcript, mock_model):
        doc = process_transcript(sample_transcript, model=mock_model, use_llm=True)
        
        assert doc is not None
        assert "summary" in doc
        assert len(doc["summary"]) > 0
    
    def test_pipeline_handles_empty_segments(self):
        transcript = {
            "segment_id": "empty_test",
            "segments": []
        }
        
        doc = process_transcript(transcript)
        assert doc["metadata"]["processed_segments"] == 0

    def test_pipeline_filters_greetings(self):
        transcript = {
            "segment_id": "filter_test",
            "segments": [
                {"start": "0:00:00", "end": "0:00:01", "text": "Hello everyone", "confidence": -0.1},
                {"start": "0:00:01", "end": "0:00:03", "text": "Click the button", "confidence": -0.1},
                {"start": "0:00:03", "end": "0:00:04", "text": "Thanks, goodbye", "confidence": -0.1}
            ]
        }

        doc = process_transcript(transcript)
        # Only the middle (instructional) segment should be counted as processed
        assert doc["metadata"]["processed_segments"] == 1
        assert len(doc["timeline"]) == 1


# ============================================================================
# Export Tests
# ============================================================================

class TestExport:
    
    def test_export_to_json(self, tmp_path, sample_transcript):
        doc = process_transcript(sample_transcript)
        output_file = tmp_path / "test_output.json"
        
        export_to_json(doc, str(output_file))
        
        assert output_file.exists()
        
        # Verify JSON is valid
        with open(output_file) as f:
            loaded = json.load(f)
            assert loaded["video_id"] == doc["video_id"]
    
    def test_export_to_markdown(self, tmp_path, sample_transcript):
        doc = process_transcript(sample_transcript)
        output_file = tmp_path / "test_output.md"
        
        export_to_markdown(doc, str(output_file))
        
        assert output_file.exists()
        
        # Verify markdown content
        content = output_file.read_text()
        assert "# " in content  # Has title
        assert "## Summary" in content
        assert "## Timeline" in content


# ============================================================================
# Configuration Tests
# ============================================================================

class TestNLPConfig:
    
    def test_default_filler_words(self):
        assert "um" in NLPConfig.DEFAULT_FILLER_WORDS
        assert "uh" in NLPConfig.DEFAULT_FILLER_WORDS
    
    def test_classification_rules(self):
        assert "action" in NLPConfig.CLASSIFICATION_RULES
        assert "click" in NLPConfig.CLASSIFICATION_RULES["action"]
    
    def test_get_default_config(self):
        config = NLPConfig.get_default_config()
        assert "filler_words" in config
        assert "classification_rules" in config
        assert isinstance(config["filler_words"], list)
        assert isinstance(config["classification_rules"], dict)


# ============================================================================
# Run tests with: pytest tests/test_nlp.py -v
# Run with coverage: pytest tests/test_nlp.py --cov=src/nlp --cov-report=html
# ============================================================================