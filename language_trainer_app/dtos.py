"""Data Transfer Objects (DTOs) for the Language Trainer application.

These are plain Python dataclasses — they are not stored in the database.
They live here rather than in ``models/`` to make it clear they are not
Django ORM models.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TestParameters:
    """DTO for test generation parameters."""

    use_adjective: bool  # Только существительное или с прилагательным
    genders: List[int]  # Род (один или много), список ID родов
    cases: List[int]  # Падеж (один или много), список ID падежей
    numbers: List[int]  # Число (один или много), список ID чисел
    animacy: Optional[str] = None  # 'Anim' / 'Inan' / None (все слова)


@dataclass
class TestItem:
    """DTO for test item returned by test generator."""

    context: str  # часть предложения до пропуска
    noun_with_adjective: str  # пара в скобках, например, "красивая машина"
    correct_answer: str  # правильный ответ в нужном падеже, например, "красивой машине"
    number_name_en: str  # English name of the word number, e.g. "Singular" / "Plural"
