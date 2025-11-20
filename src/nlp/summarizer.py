from typing import List, Dict

class Summarizer:
    def __init__(self, model=None):
        self.model = model  # LLM model wrapper if available

    def summarize_text(self, passages: List[str]) -> str:
        text = " ".join(passages).strip()

        if not self.model:
            # fallback summarization heuristic
            return text[:180] + "..." if len(text) > 200 else text

        # With LLM
        prompt = (
            "Summarize the following spoken instructions into one concise sentence:\n"
            + text
        )
        return self.model.generate(prompt)

    def summarize_segments(self, segments: List[Dict]) -> str:
        texts = [s["text"] for s in segments if len(s["text"]) > 0]
        return self.summarize_text(texts)
