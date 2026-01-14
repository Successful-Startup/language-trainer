from dataclasses import dataclass


@dataclass
class TestItem:
    """DTO for test item returned by test generator."""

    context: str  # часть предложения до пропуска
    noun_with_adjective: str  # пара в скобках, например, "красивая машина"
    correct_answer: str  # правильный ответ в нужном падеже, например, "красивой машине"
