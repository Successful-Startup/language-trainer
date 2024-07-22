# Desc: URL configuration for the language_trainer_app
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from language_trainer_app.controllers import WordViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'', WordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
