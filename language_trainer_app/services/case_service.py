
from language_trainer_app.repositories.cases_repository import CaseRepository


class CaseService:
    @staticmethod
    def get_all_cases():
        return CaseRepository.get_all_cases()