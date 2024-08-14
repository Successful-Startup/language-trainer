from language_trainer_app.models.part_of_speech import PartOfSpeech


class PartOfSpeechService:

    @staticmethod
    def get_all_parts_of_speech():
        return PartOfSpeech.objects.all()
