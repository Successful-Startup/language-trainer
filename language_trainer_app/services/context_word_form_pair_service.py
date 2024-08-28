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
    def update_context_word_form_pair(context_word_form_pair_id, context_word_form_pair_data):
        return ContextWordFormPair.objects.get(id=context_word_form_pair_id).update(**context_word_form_pair_data)

    @staticmethod
    def delete_context_word_form_pair(context_word_form_pair_id):
        return ContextWordFormPair.objects.filter(id=context_word_form_pair_id).delete()
