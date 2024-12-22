from typing import List
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair


class ContextWordFormPairService:
    @staticmethod
    def get_all_context_word_form_pairs():
        return ContextWordFormPair.objects.all()

    @staticmethod
    def get_context_word_form_pair_by_id(context_word_form_pair_id):
        return ContextWordFormPair.objects.get(id=context_word_form_pair_id)

    @staticmethod
    def create_context_word_form_pair(context_word_form_pair_data):
        return ContextWordFormPair.objects.create(**context_word_form_pair_data)

    @staticmethod
    def update_context_word_form_pair(
        context_word_form_pair_id, context_word_form_pair_data
    ):
        return ContextWordFormPair.objects.get(id=context_word_form_pair_id).update(
            **context_word_form_pair_data
        )

    @staticmethod
    def delete_context_word_form_pair(context_word_form_pair_id):
        return ContextWordFormPair.objects.filter(id=context_word_form_pair_id).delete()

    def get_by_params(
        self,
        use_adjective: bool,
        genders: List[int],
        cases: List[int],
        numbers: List[int],
    ):
        # 1. Фильтруем пары по параметрам рода, числа и падежа
        query = ContextWordFormPair.objects.filter(
            noun_form__gender__in=genders,
            noun_form__case__in=cases,
            noun_form__number__in=numbers,
        )

        # 2. Если нужно использовать прилагательное, добавляем фильтр по прилагательным
        if use_adjective:
            query = query.filter(
                adjective_form__gender__in=genders,
                adjective_form__case__in=cases,
                adjective_form__number__in=numbers,
            )

        # 3. Возвращаем список подходящих пар
        return query.all()
