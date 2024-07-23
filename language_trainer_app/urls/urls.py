# Desc: URL configuration for the language_trainer_app
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from language_trainer_app.controllers import WordViewSet
from language_trainer_app.controllers.gender_controller import GenderViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'words', WordViewSet)
router.register(r'genders', GenderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
