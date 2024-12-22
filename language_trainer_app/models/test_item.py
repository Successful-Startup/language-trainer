class TestItem:
    def __init__(self, context: str, noun_with_adjective: str, correct_answer: str):
        self.context = context  # часть предложения до пропуска
        self.noun_with_adjective = (
            noun_with_adjective  # пара в скобках, например, "красивая машина"
        )
        self.correct_answer = correct_answer  # правильный ответ в нужном падеже, например, "красивой машине"
