from LanguageTrainerApp.repositories.word_repository import WordRepository

class WordService:
    @staticmethod
    def get_all_words():
        return WordRepository.get_all_words()

    @staticmethod
    def get_word_by_id(word_id):
        return WordRepository.get_word_by_id(word_id)

    @staticmethod
    def create_word(word_data):
        return WordRepository.create_word(word_data)

    @staticmethod
    def update_word(word_id, word_data):
        return WordRepository.update_word(word_id, word_data)

    @staticmethod
    def delete_word(word_id):
        return WordRepository.delete_word(word_id)
