import random
from typing import List

from language_trainer_app.models.test_item import TestItem
from language_trainer_app.models.test_parameters import TestParameters
from language_trainer_app.services.context_word_form_pair_service import (
    ContextWordFormPairService,
)


class TestGeneratorService:
    def __init__(self, context_word_form_pair_service: ContextWordFormPairService):
        self.context_word_form_pair_service = context_word_form_pair_service

    def generate_test(self, test_params: TestParameters) -> TestItem:
        # 1. Получаем список всех доступных ContextWordFormPair с учётом параметров теста
        word_form_pairs = self.context_word_form_pair_service.get_by_params(
            use_adjective=test_params.use_adjective,
            genders=test_params.genders,
            cases=test_params.cases,
            numbers=test_params.numbers,
        )

        # 2. Случайно выбираем одну подходящую пару
        selected_pair = random.choice(word_form_pairs)

        # 3. Формируем данные для теста
        context = selected_pair.context.text

        if test_params.use_adjective:
            # Формируем строку для отображения в скобках (например, "красивая машина")
            noun_with_adjective = f"{selected_pair.adjective_form.word.base_form} {selected_pair.noun_form.word.base_form}"
            # Формируем правильный ответ (например, "красивой машине")
            correct_answer = f"{selected_pair.adjective_form.word_form} {selected_pair.noun_form.word_form}"
        else:
            # Формируем строку для отображения только с существительным
            noun_with_adjective = selected_pair.noun_form.word.base_form
            correct_answer = selected_pair.noun_form.word_form

        # 4. Возвращаем объект теста
        return TestItem(
            context=context,
            noun_with_adjective=noun_with_adjective,
            correct_answer=correct_answer,
        )
