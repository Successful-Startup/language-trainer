# Desc: URL configuration for the LanguageTrainerApp
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from LanguageTrainerApp.views import WordViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'words', WordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
