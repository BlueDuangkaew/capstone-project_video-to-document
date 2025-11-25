"""
Document Structurer Module
Assembles processed data into structured hierarchical documentation
with metadata, statistics, and proper formatting
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DocumentStructurer:
    """Assemble processed data into structured documentation"""
    
    def build_document(
        self,
        transcript: Dict,
        cleaned_segments: List[Dict],
        classified_segments: List[Dict],
        steps: List[str],
        summary: str
    ) -> Dict:
        """
        Build final structured document
        
        Args:
            transcript: Original transcript JSON
            cleaned_segments: Cleaned segments
            classified_segments: Classified segments
            steps: Extracted steps
            summary: Generated summary
            
        Returns:
            Structured document dictionary
        """
        # Generate title from segment_id or first meaningful text
        video_id = transcript.get("segment_id", "unknown")
        title = self._generate_title(classified_segments, video_id)
        
        # Build timeline with all relevant data
        timeline = self._build_timeline(classified_segments)
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(classified_segments)
        
        # Calculate statistics
        stats = self._calculate_stats(transcript, classified_segments)
        
        return {
            "video_id": video_id,
            "title": title,
            "summary": summary,
            "steps": steps,
            "key_concepts": key_concepts,
            "timeline": timeline,
            "statistics": stats,
            "metadata": {
                "model": transcript.get("model"),
                "language": transcript.get("language"),
                "duration": transcript.get("duration"),
                "video_path": transcript.get("video_path"),
                "processed_segments": len(classified_segments),
                "original_segments": len(transcript.get("segments", [])),
            }
        }
    
    def _generate_title(self, segments: List[Dict], fallback: str) -> str:
        """
        Generate document title from content
        
        Args:
            segments: List of classified segments
            fallback: Fallback title if generation fails
            
        Returns:
            Generated title string
        """
        # Look for first explanation or statement
        for seg in segments:
            if seg.get("label") in ("explanation", "statement"):
                text = seg.get("text", "")
                if len(text) > 20:
                    # Use first sentence as title
                    title = text.split('.')[0]
                    if len(title) > 60:
                        title = title[:57] + "..."
                    return title
        
        return f"Documentation for {fallback}"
    
    def _build_timeline(self, segments: List[Dict]) -> List[Dict]:
        """
        Build detailed timeline with all segment data
        
        Args:
            segments: List of classified segments
            
        Returns:
            List of timeline entries
        """
        timeline = []
        for seg in segments:
            timeline.append({
                "start": seg.get("start_seconds", 0),
                "end": seg.get("end_seconds", 0),
                "start_formatted": seg.get("start", "0:00:00"),
                "end_formatted": seg.get("end", "0:00:00"),
                "text": seg.get("text", ""),
                "label": seg.get("label", "unknown"),
                "label_source": seg.get("label_source", "unknown"),
                "confidence": seg.get("confidence", 0),
                "segment_index": seg.get("segment_index", -1)
            })
        return timeline
    
    def _extract_key_concepts(self, segments: List[Dict]) -> List[str]:
        """
        Extract key concepts mentioned in the transcript
        
        Args:
            segments: List of classified segments
            
        Returns:
            List of key concept strings
        """
        concepts = []
        for seg in segments:
            if seg.get("label") == "definition":
                concepts.append(seg.get("text", ""))
        return concepts[:10]  # Limit to top 10
    
    def _calculate_stats(self, transcript: Dict, 
                        segments: List[Dict]) -> Dict:
        """
        Calculate statistics about the document
        
        Args:
            transcript: Original transcript
            segments: Processed segments
            
        Returns:
            Statistics dictionary
        """
        label_counts = {}
        for seg in segments:
            label = seg.get("label", "unknown")
            label_counts[label] = label_counts.get(label, 0) + 1
        
        total_words = sum(
            len(seg.get("text", "").split()) 
            for seg in segments
        )
        
        return {
            "total_segments": len(segments),
            "total_words": total_words,
            "label_distribution": label_counts,
            "avg_segment_length": total_words / len(segments) if segments else 0
        }
    