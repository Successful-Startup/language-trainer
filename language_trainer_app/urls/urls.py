# Desc: URL configuration for the language_trainer_app
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from language_trainer_app.controllers import WordViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'words', WordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
