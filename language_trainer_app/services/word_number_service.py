from language_trainer_app.models.word_number import WordNumber


class WordNumberService:

    @staticmethod
    def get_all_word_numbers():
        return WordNumber.objects.all()
