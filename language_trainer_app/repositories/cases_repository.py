from language_trainer_app.models.case import Case

class CaseRepository:
    @staticmethod
    def get_all_cases():
        return Case.objects.all()