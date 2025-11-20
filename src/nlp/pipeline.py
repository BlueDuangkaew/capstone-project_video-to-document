from src.nlp.text_cleaner import TextCleaner
from src.nlp.segment_classifier import SegmentClassifier
from src.nlp.summarizer import Summarizer
from src.nlp.step_extractor import StepExtractor
from src.nlp.doc_structurer import DocumentStructurer

def process_transcript(transcript_json: dict, model=None):
    cleaner = TextCleaner()
    classifier = SegmentClassifier(model=model)
    summarizer = Summarizer(model=model)
    stepper = StepExtractor(model=model)
    structurer = DocumentStructurer()

    cleaned = cleaner.clean_segments(transcript_json["segments"])
    classified = classifier.classify_segments(cleaned)
    summary = summarizer.summarize_segments(classified)
    steps = stepper.extract_steps(classified)

    document = structurer.build_document(
        transcript_json,
        cleaned,
        classified,
        steps,
        summary
    )

    return document
