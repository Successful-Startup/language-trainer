from language_trainer_app.models.word import Word


class WordService:
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
        instance = Word.objects.get(id=word_id)
        for key, value in word_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    @staticmethod
    def delete_word(word_id):
        return Word.objects.filter(id=word_id).delete()
