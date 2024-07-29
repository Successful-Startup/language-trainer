
from language_trainer_app.models.gender import Gender


class GenderService:
    @staticmethod
    def get_all_genders():
        return Gender.objects.all()