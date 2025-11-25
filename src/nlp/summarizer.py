"""
Summarizer Module
Generates summaries from transcript segments using either rule-based
methods or LLM-based intelligent summarization
"""

import re
import logging
from typing import List, Dict, Optional, Protocol

from .nlp_config import NLPConfig

logger = logging.getLogger(__name__)


class LLMModel(Protocol):
    """Protocol for LLM model wrappers"""
    def generate(self, prompt: str) -> str:
        """Generate text completion from prompt"""
        ...


class Summarizer:
    """Generate summaries from transcript segments"""
    
    def __init__(self, model: Optional[LLMModel] = None):
        """
        Initialize summarizer
        
        Args:
            model: Optional LLM model for intelligent summarization
        """
        self.model = model
    
    def _rule_based_summary(self, text: str, max_sentences: int = 3) -> str:
        """
        Create summary using simple heuristics
        """
        if not text:
            return ""

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        # Take first N sentences
        selected = sentences[:max_sentences]

        # Join back with ". " (preserve punctuation already present)
        summary = " ".join(selected).strip()

        return summary

    
    def summarize_text(self, passages: List[str], 
                      use_llm: bool = True) -> str:
        """
        Summarize a list of text passages
        
        Args:
            passages: List of text strings to summarize
            use_llm: Whether to use LLM for summarization
            
        Returns:
            Summary text
        """
        if not passages:
            return ""
        
        # Combine passages
        text = " ".join(p for p in passages if p).strip()
        
        if not text:
            return ""
        
        # Use LLM if available and requested
        if use_llm and self.model:
            try:
                prompt = f"""Summarize the following spoken instructions into 2-3 concise sentences.
Focus on the main actions and key concepts discussed.

Text:
{text}

Summary:"""
                return self.model.generate(prompt).strip()
            except Exception as e:
                logger.error(f"LLM summarization failed: {e}")
                # Fall through to rule-based
        
        # Fallback to rule-based
        return self._rule_based_summary(text, max_sentences=NLPConfig.SUMMARY_SENTENCE_LIMIT)
    
    def summarize_segments(self, segments: List[Dict], 
                          use_llm: bool = True) -> str:
        """
        Summarize classified segments
        
        Args:
            segments: List of classified segment dicts
            use_llm: Whether to use LLM
            
        Returns:
            Overall summary
        """
        if not segments:
            return "No content to summarize."
        
        # Extract meaningful text (exclude noise)
        texts = [
            s["text"] 
            for s in segments 
            if s.get("text") and s.get("label") != "noise"
        ]
        
        return self.summarize_text(texts, use_llm=use_llm)
