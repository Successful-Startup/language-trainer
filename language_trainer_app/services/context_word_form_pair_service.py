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
        instance = ContextWordFormPair.objects.get(id=context_word_form_pair_id)
        for key, value in context_word_form_pair_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

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

        # 2. Фильтруем по использованию прилагательного
        if use_adjective:
            # Если нужны прилагательные, берем только пары с adjective_form и проверяем их параметры
            query = query.filter(
                adjective_form__isnull=False,
                adjective_form__gender__in=genders,
                adjective_form__case__in=cases,
                adjective_form__number__in=numbers,
            )
        else:
            # Если прилагательные НЕ нужны, берем только пары БЕЗ adjective_form
            query = query.filter(adjective_form__isnull=True)

        # 3. Возвращаем QuerySet подходящих пар
        return query
