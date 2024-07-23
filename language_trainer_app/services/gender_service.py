
from language_trainer_app.repositories.gender_repository import GenderRepository


class GenderService:
    @staticmethod
    def get_all_genders():
        return GenderRepository.get_all_genders()