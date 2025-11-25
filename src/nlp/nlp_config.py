"""
Configuration module for NLP processing pipeline
Contains default settings, rules, and configuration management
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class NLPConfig:
    """Configuration for NLP processing"""
    
    DEFAULT_FILLER_WORDS = [
        "um", "uh", "like", "you know", "sort of", "kind of",
        "i mean", "basically", "actually", "literally",
        "[music]", "[noise]", "[laughter]", "(laughs)", "(applause)",
        "uh-huh", "mm-hmm"
    ]
    
    CLASSIFICATION_RULES = {
        # greetings and closing phrases are handled specially so they can be
        # filtered out prior to building the final document
        "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "welcome"],
        "farewell": ["thanks", "thank you", "goodbye", "bye", "see you", "see ya", "take care", "cheers"],
        "action": ["click", "open", "select", "go to", "press", "drag", 
                   "type", "enter", "choose", "navigate", "scroll"],
        "explanation": ["so", "basically", "this is", "what happens", "because",
                       "the reason", "essentially"],
        "question": ["how do", "what is", "why does", "can i", "should i"],
        "transition": ["next", "now", "then", "after that", "moving on",
                      "let's", "okay so"],
        "definition": ["this is", "we call this", "defined as", "means",
                      "refers to"]
    }
    
    MIN_CONFIDENCE = -1.0  # Minimum confidence threshold
    MIN_SEGMENT_LENGTH = 3  # Minimum characters for valid segment
    SUMMARY_SENTENCE_LIMIT = 3  # Max sentences in rule-based summary
    
    @classmethod
    def load_from_file(cls, config_path: str) -> Dict:
        """
        Load configuration from JSON file
        
        Args:
            config_path: Path to configuration JSON file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    @classmethod
    def save_to_file(cls, config: Dict, config_path: str):
        """
        Save configuration to JSON file
        
        Args:
            config: Configuration dictionary to save
            config_path: Path where to save the configuration
        """
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_default_config(cls) -> Dict:
        """
        Get default configuration as dictionary
        
        Returns:
            Default configuration dictionary
        """
        return {
            "filler_words": cls.DEFAULT_FILLER_WORDS,
            "classification_rules": cls.CLASSIFICATION_RULES,
            "min_confidence": cls.MIN_CONFIDENCE,
            "min_segment_length": cls.MIN_SEGMENT_LENGTH,
            "summary_sentence_limit": cls.SUMMARY_SENTENCE_LIMIT
        }
    