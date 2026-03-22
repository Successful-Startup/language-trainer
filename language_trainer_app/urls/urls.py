# URL configuration for the language_trainer_app
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from language_trainer_app.controllers import WordViewSet, import_controller
from language_trainer_app.controllers.gender_controller import GenderViewSet
from language_trainer_app.controllers.case_controller import CaseViewSet
from language_trainer_app.controllers.part_of_speech_controller import (
    PartOfSpeechViewSet,
)
from language_trainer_app.controllers.test_controller import TestViewSet
from language_trainer_app.controllers.word_number_controller import WordNumberViewSet
from language_trainer_app.controllers.word_form_controller import WordFormViewSet
from language_trainer_app.controllers.context_controller import ContextViewSet
from language_trainer_app.controllers.context_word_form_pair_controller import (
    ContextWordFormPairViewSet,
)

# Use Django standard trailing slash (True by default)
router = DefaultRouter()
router.register(r"words", WordViewSet)
router.register(r"genders", GenderViewSet)
router.register(r"cases", CaseViewSet)
router.register(r"parts-of-speech", PartOfSpeechViewSet)
router.register(r"word-numbers", WordNumberViewSet)
router.register(r"word-forms", WordFormViewSet)
router.register(r"contexts", ContextViewSet)
router.register(r"context-word-form-pairs", ContextWordFormPairViewSet)
router.register(r"tests", TestViewSet, basename="test")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # CSV Import endpoints
    path("api/import/words/", import_controller.import_words, name="import-words"),
    path(
        "api/import/contexts/",
        import_controller.import_contexts,
        name="import-contexts",
    ),
    path(
        "api/import/word-forms/",
        import_controller.import_word_forms,
        name="import-word-forms",
    ),
]
