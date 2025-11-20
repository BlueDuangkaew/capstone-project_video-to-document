import re
from typing import List, Dict

class TextCleaner:
    def __init__(self):
        filler_words = [
            "um", "uh", "like", "you know", "sort of", "kind of",
            "[music]", "[noise]", "(laughs)", "(applause)"
        ]
        self.filler_pattern = re.compile(
            r"\b(" + "|".join(map(re.escape, filler_words)) + r")\b",
            flags=re.IGNORECASE
        )

    def clean_text(self, text: str) -> str:
        text = text.strip()

        # Remove filler words
        text = self.filler_pattern.sub("", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Fix capitalization
        if text and text[0].islower():
            text = text[0].upper() + text[1:]

        return text

    def clean_segments(self, segments: List[Dict]) -> List[Dict]:
        cleaned = []
        for seg in segments:
            new_seg = dict(seg)
            new_seg["text"] = self.clean_text(seg["text"])
            cleaned.append(new_seg)
        return cleaned
