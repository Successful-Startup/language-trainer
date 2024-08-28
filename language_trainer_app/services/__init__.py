from .word_service import WordService
from .gender_service import GenderService
from .case_service import CaseService
from .part_of_speech_service import PartOfSpeechService
from .word_number_service import WordNumberService
from .word_form_service import WordFormService
from .context_service import ContextService
from .context_word_form_pair_service import ContextWordFormPairService

__all__ = [
    "WordService",
    "GenderService",
    "CaseService",
    "PartOfSpeechService",
    "WordNumberService",
    "WordFormService",
    "ContextService",
    "ContextWordFormPairService",
]
