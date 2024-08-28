from language_trainer_app.models.context import Context


class ContextService:
    @staticmethod
    def get_all_contexts():
        return Context.objects.all()

    @staticmethod
    def get_context_by_id(context_id):
        return Context.objects.get(id=context_id)

    @staticmethod
    def create_context(context_data):
        return Context.objects.create(**context_data)

    @staticmethod
    def update_context(context_id, context_data):
        return Context.objects.get(id=context_id).update(**context_data)

    @staticmethod
    def delete_context(context_id):
        return Context.objects.filter(id=context_id).delete()
