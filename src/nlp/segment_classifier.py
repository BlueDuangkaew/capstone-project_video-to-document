"""
Segment Classifier Module
Classifies transcript segments into categories like action, explanation,
question, transition, definition, etc.
"""

import re
import logging
from typing import Dict, List, Optional, Protocol

from .nlp_config import NLPConfig

logger = logging.getLogger(__name__)


class LLMModel(Protocol):
    """Protocol for LLM model wrappers"""
    def generate(self, prompt: str) -> str:
        """Generate text completion from prompt"""
        ...
    
    def generate_list(self, prompt: str) -> List[str]:
        """Generate a list of items from prompt"""
        ...


class SegmentClassifier:
    """Classify transcript segments into categories"""
    
    def __init__(self, model: Optional[LLMModel] = None, 
                 rules: Optional[Dict[str, List[str]]] = None):
        """
        Initialize classifier
        
        Args:
            model: Optional LLM model for intelligent classification
            rules: Custom classification rules. If None, uses defaults.
        """
        self.model = model
        self.rules = rules or NLPConfig.CLASSIFICATION_RULES
        
    def classify(self, text: str, confidence: float = 0.0) -> str:
        """
        Classify a single text segment
        
        Args:
            text: Text to classify
            confidence: Whisper confidence score
            
        Returns:
            Classification label
        """
        if not text:
            return "noise"
        
        text_lower = text.lower()
        
        # Check for noise based on confidence and length
        if confidence < NLPConfig.MIN_CONFIDENCE or len(text) < 3:
            return "noise"
        
        # Rule-based classification
        for label, keywords in self.rules.items():
            if any(keyword in text_lower for keyword in keywords):
                return label
        
        # Check for questions
        if text_lower.strip().endswith("?"):
            return "question"
        
        # Default classification
        return "statement"
    
    def classify_with_llm(self, segments: List[Dict]) -> List[Dict]:
        """
        Use LLM for more sophisticated classification
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Segments with LLM-based labels
        """
        if not self.model:
            raise ValueError("No LLM model provided for LLM classification")
        
        # Batch segments for efficient processing
        text_batch = "\n".join([
            f"{i}. {seg['text']}" 
            for i, seg in enumerate(segments)
        ])
        
        prompt = f"""Classify each of the following spoken segments into one of these categories:
- action: UI interactions or commands
- explanation: Describing concepts or reasoning
- question: Asking a question
- transition: Moving between topics
- definition: Defining terms
- statement: General statements
- noise: Irrelevant or unclear content

Segments:
{text_batch}

Respond with only the segment number and label, one per line (e.g., "0. action")"""
        
        try:
            response = self.model.generate(prompt)
            labels = self._parse_llm_labels(response)
            
            for i, seg in enumerate(segments):
                seg["label"] = labels.get(i, "statement")
                seg["label_source"] = "llm"
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to rule-based
            for seg in segments:
                seg["label"] = self.classify(seg["text"], seg.get("confidence", 0))
                seg["label_source"] = "rules"
        
        return segments
    
    def _parse_llm_labels(self, response: str) -> Dict[int, str]:
        """Parse LLM response into segment index -> label mapping"""
        labels = {}
        for line in response.strip().split("\n"):
            match = re.match(r"(\d+)\.\s*(\w+)", line)
            if match:
                idx, label = match.groups()
                labels[int(idx)] = label.lower()
        return labels
    
    def classify_segments(self, segments: List[Dict], 
                         use_llm: bool = False) -> List[Dict]:
        """
        Classify all segments
        
        Args:
            segments: List of cleaned segments
            use_llm: Whether to use LLM for classification
            
        Returns:
            Classified segments
        """
        if not segments:
            logger.warning("No segments to classify")
            return []
        
        if use_llm and self.model:
            return self.classify_with_llm(segments)
        
        # Rule-based classification
        classified = []
        for seg in segments:
            try:
                new_seg = dict(seg)
                new_seg["label"] = self.classify(
                    seg.get("text", ""),
                    seg.get("confidence", 0.0)
                )
                new_seg["label_source"] = "rules"
                classified.append(new_seg)
            except Exception as e:
                logger.error(f"Error classifying segment: {e}")
                continue
        
        logger.info(f"Classified {len(classified)} segments")
        return classified