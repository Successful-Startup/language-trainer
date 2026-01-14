from dataclasses import dataclass
from typing import List


@dataclass
class TestParameters:
    """DTO for test generation parameters."""

    use_adjective: bool  # Только существительное или с прилагательным
    genders: List[int]  # Род (один или много), список ID родов
    cases: List[int]  # Падеж (один или много), список ID падежей
    numbers: List[int]  # Число (один или много), список ID чисел
