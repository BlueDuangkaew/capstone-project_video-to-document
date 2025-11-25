"""
Step Extractor Module
Extracts actionable steps from transcript segments for documentation
"""

import re
import logging
from typing import List, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class LLMModel(Protocol):
    """Protocol for LLM model wrappers"""
    def generate(self, prompt: str) -> str:
        """Generate text completion from prompt"""
        ...
    
    def generate_list(self, prompt: str) -> List[str]:
        """Generate a list of items from prompt"""
        ...


class StepExtractor:
    """Extract actionable steps from transcript"""
    
    def __init__(self, model: Optional[LLMModel] = None):
        """
        Initialize step extractor
        
        Args:
            model: Optional LLM model for intelligent extraction
        """
        self.model = model
    
    def _merge_similar_steps(self, steps: List[str]) -> List[str]:
        """
        Merge very similar consecutive steps
        
        Args:
            steps: List of step strings
            
        Returns:
            Merged list of steps
        """
        if len(steps) <= 1:
            return steps
        
        merged = [steps[0]]
        for step in steps[1:]:
            # Check if very similar to last step
            last = merged[-1].lower()
            current = step.lower()
            
            # Simple similarity check
            if current not in last and last not in current:
                merged.append(step)
        
        return merged
    
    def extract_steps(self, segments: List[Dict], 
                     use_llm: bool = False) -> List[str]:
        """
        Extract actionable steps from segments
        
        Args:
            segments: List of classified segments
            use_llm: Whether to use LLM for extraction
            
        Returns:
            List of step descriptions
        """
        if not segments:
            logger.warning("No segments to extract steps from")
            return []
        
        # Rule-based: extract action-labeled segments
        steps = []
        for seg in segments:
            label = seg.get("label", "")
            text = seg.get("text", "")
            
            if label in ("action", "instruction") and text:
                steps.append(text)
        
        # If no steps found and LLM available, use LLM
        if not steps and use_llm and self.model:
            try:
                all_text = "\n".join(s["text"] for s in segments if s.get("text"))
                prompt = f"""Extract clear, actionable steps from the following spoken text.
Return only the steps, numbered, one per line.
Focus on concrete actions the user should take.

Text:
{all_text}

Steps:"""
                response = self.model.generate(prompt)
                steps = self._parse_llm_steps(response)
            except Exception as e:
                logger.error(f"LLM step extraction failed: {e}")
        
        # Merge similar steps
        steps = self._merge_similar_steps(steps)
        
        logger.info(f"Extracted {len(steps)} steps")
        return steps
    
    def _parse_llm_steps(self, response: str) -> List[str]:
        """
        Parse LLM response into list of steps
        
        Args:
            response: LLM generated response
            
        Returns:
            List of step strings
        """
        steps = []
        for line in response.strip().split("\n"):
            # Remove numbering
            line = re.sub(r"^\d+\.\s*", "", line).strip()
            if line:
                steps.append(line)
        return steps
    