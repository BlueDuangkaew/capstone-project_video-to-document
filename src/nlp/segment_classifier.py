from typing import Dict, List

class SegmentClassifier:
    def __init__(self, model=None):
        """
        model: optional LLM wrapper (OpenAI, local).
        If None, fallback to simple rules.
        """
        self.model = model

    def classify(self, text: str) -> str:
        text_lower = text.lower()

        # rule-based classification
        if any(x in text_lower for x in ["click", "open", "select", "go to", "press"]):
            return "action"
        if text_lower.startswith("so") or text_lower.startswith("basically"):
            return "explanation"
        if len(text_lower) < 5:
            return "noise"

        # fallback
        return "statement"

    def classify_segments(self, segments: List[Dict]) -> List[Dict]:
        out = []
        for seg in segments:
            new_seg = dict(seg)
            new_seg["label"] = self.classify(seg["text"])
            out.append(new_seg)
        return out
