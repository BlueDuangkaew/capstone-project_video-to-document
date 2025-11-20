from src.nlp.text_cleaner import TextCleaner
from src.nlp.segment_classifier import SegmentClassifier
from src.nlp.step_extractor import StepExtractor
from src.nlp.summarizer import Summarizer
from src.nlp.doc_structurer import DocumentStructurer

def test_cleaner():
    cleaner = TextCleaner()
    text = "um click the button  "
    assert cleaner.clean_text(text) == "Click the button"

def test_classifier():
    classifier = SegmentClassifier()
    seg = classifier.classify("Click on the file")
    assert seg == "action"

def test_step_extractor():
    stepper = StepExtractor()
    segments = [{"text":"Click OK","label":"action"}]
    steps = stepper.extract_steps(segments)
    assert steps == ["Click OK"]

def test_document_build():
    struct = DocumentStructurer()
    doc = struct.build_document(
        {"segment_id":"abc"},
        [],
        [{"start_global":0,"end_global":1,"text":"Click OK","label":"action"}],
        ["Click OK"],
        "summary text"
    )
    assert "summary" in doc
    assert len(doc["steps"]) == 1
