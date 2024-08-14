from language_trainer_app.models.word_form import WordForm


class WordFormService:
    @staticmethod
    def get_all_word_forms():
        return WordForm.objects.all()

    @staticmethod
    def get_word_form_by_id(word_form_id):
        return WordForm.objects.get(id=word_form_id)

    @staticmethod
    def create_word_form(word_form_data):
        return WordForm.objects.create(**word_form_data)

    @staticmethod
    def update_word_form(word_form_id, word_form_data):
        return WordForm.objects.get(id=word_form_id).update(**word_form_data)

    @staticmethod
    def delete_word_form(word_form_id):
        return WordForm.objects.filter(id=word_form_id).delete()
