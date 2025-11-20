# src/nlp/step_extractor.py

from typing import List, Dict

class StepExtractor:
    def __init__(self, model=None):
        self.model = model

    def extract_steps(self, segments: List[Dict]) -> List[str]:
        steps = []

        for seg in segments:
            if seg.get("label") == "action":
                steps.append(seg["text"])

        if not steps and self.model:
            # fallback: ask LLM to extract steps
            prompt = (
                "Extract actionable steps from the following spoken text:\n" +
                "\n".join(s["text"] for s in segments)
            )
            steps = self.model.generate_list(prompt)

        return steps
