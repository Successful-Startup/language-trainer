from typing import List


class TestParameters:
    use_adjective: bool  # Только существительное или с прилагательным
    genders: List[int]  # Род (один или много), список ID родов
    cases: List[int]  # Падеж (один или много), список ID падежей
    numbers: List[int]  # Число (один или много), список ID чисел

    def __init__(
        self,
        use_adjective: bool,
        genders: List[int],
        cases: List[int],
        numbers: List[int],
    ):
        self.use_adjective = use_adjective
        self.genders = genders
        self.cases = cases
        self.numbers = numbers
