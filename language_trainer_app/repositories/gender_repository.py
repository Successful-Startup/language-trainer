from language_trainer_app.models.gender import Gender

class GenderRepository:
    @staticmethod
    def get_all_genders():
        return Gender.objects.all()