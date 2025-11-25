"""
Text Cleaner Module
Cleans and normalizes Whisper transcripts by removing filler words,
normalizing whitespace, and parsing timestamps
"""

import re
import logging
from typing import List, Dict, Optional

from .nlp_config import NLPConfig

logger = logging.getLogger(__name__)


class TextCleaner:
    """Clean and normalize Whisper transcripts"""
    
    def __init__(self, filler_words: Optional[List[str]] = None):
        """
        Initialize text cleaner
        
        Args:
            filler_words: List of words to remove. If None, uses defaults.
        """
        if filler_words is None:
            filler_words = NLPConfig.DEFAULT_FILLER_WORDS
        
        self.filler_pattern = re.compile(
            r"\b(" + "|".join(map(re.escape, filler_words)) + r")\b",
            flags=re.IGNORECASE
        )
        
    def clean_text(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return ""

        # Strip leading/trailing whitespace
        text = text.strip()

        # Remove bracketed tags like [music], [applause], [noise]
        text = re.sub(r"\[.*?\]", "", text)

        # Remove filler words
        text = self.filler_pattern.sub("", text)

        # Normalize whitespace (multiple spaces to single space)
        text = re.sub(r"\s+", " ", text).strip()

        # Remove standalone punctuation artifacts
        text = re.sub(r"\s+([.,!?])", r"\1", text)

        # Fix capitalization - only if text is non-empty
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]

        # Ensure proper sentence ending
        if text and text[-1] not in ".!?":
            text += "."

        return text
    
    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Convert timestamp string to seconds
        
        Args:
            timestamp: Time string in format "H:MM:SS" or "M:SS"
            
        Returns:
            Time in seconds
        """
        try:
            parts = timestamp.split(":")
            if len(parts) == 3:  # H:MM:SS
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:  # M:SS
                m, s = map(float, parts)
                return m * 60 + s
            else:
                return 0.0
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse timestamp: {timestamp}")
            return 0.0
    
    def clean_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Clean all segments in a transcript
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            List of cleaned segments with additional fields
        """
        if not segments:
            logger.warning("No segments to clean")
            return []
        
        cleaned = []
        
        for i, seg in enumerate(segments):
            try:
                # Create new segment dict
                new_seg = dict(seg)
                
                # Clean the text
                original_text = seg.get("text", "")
                cleaned_text = self.clean_text(original_text)
                new_seg["text"] = cleaned_text
                new_seg["original_text"] = original_text
                
                # Parse timestamps to seconds
                start_str = seg.get("start", "0:00:00")
                end_str = seg.get("end", "0:00:00")
                new_seg["start_seconds"] = self._parse_timestamp(start_str)
                new_seg["end_seconds"] = self._parse_timestamp(end_str)
                
                # Add segment index
                new_seg["segment_index"] = i
                
                # Only add if segment has meaningful content
                # Strip the added period to check actual content length
                content_without_period = cleaned_text.rstrip('.')
                if len(content_without_period) >= NLPConfig.MIN_SEGMENT_LENGTH:
                    cleaned.append(new_seg)
                else:
                    logger.debug(f"Skipped short segment: '{cleaned_text}'")
                    
            except Exception as e:
                logger.error(f"Error cleaning segment {i}: {e}")
                continue
        
        logger.info(f"Cleaned {len(cleaned)} segments from {len(segments)} original")
        return cleaned
    