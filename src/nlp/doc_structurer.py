from typing import Dict, List

class DocumentStructurer:
    def build_document(
        self,
        transcript: Dict,
        cleaned_segments: List[Dict],
        classified_segments: List[Dict],
        steps: List[str],
        summary: str
    ) -> Dict:

        return {
            "video_id": transcript["segment_id"],
            "title": f"Documentation for {transcript['segment_id']}",
            "summary": summary,
            "steps": steps,
            "timeline": [
                {
                    "start": s.get("start_global"),
                    "end": s.get("end_global"),
                    "text": s.get("text"),
                    "label": s.get("label"),
                }
                for s in classified_segments
            ],
            "metadata": {
                "model": transcript.get("model"),
                "language": transcript.get("language"),
                "duration": transcript.get("duration"),
            }
        }
