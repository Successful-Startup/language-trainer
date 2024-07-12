from language_trainer_app.models.word import Word

class WordRepository:
    @staticmethod
    def get_all_words():
        return Word.objects.all()

    @staticmethod
    def get_word_by_id(word_id):
        return Word.objects.get(id=word_id)

    @staticmethod
    def create_word(word_data):
        return Word.objects.create(**word_data)

    @staticmethod
    def update_word(word_id, word_data):
        Word.objects.filter(id=word_id).update(**word_data)
        return Word.objects.get(id=word_id)

    @staticmethod
    def delete_word(word_id):
        Word.objects.filter(id=word_id).delete()
