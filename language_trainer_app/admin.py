from django.contrib import admin

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.context_word_form_pair import ContextWordFormPair
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.phrase import Phrase
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(PartOfSpeech)
class PartOfSpeechAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(WordNumber)
class WordNumberAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ["id", "base_form", "gender", "part_of_speech", "animacy"]
    list_filter = ["gender", "part_of_speech", "animacy"]
    search_fields = ["base_form"]
    ordering = ["base_form"]
    show_full_result_count = False

    class Media:
        js = ("language_trainer_app/admin/live_search.js",)


@admin.register(WordForm)
class WordFormAdmin(admin.ModelAdmin):
    list_display = ["id", "word_form", "word", "case", "gender", "number"]
    list_filter = ["case", "gender", "number"]
    search_fields = ["word_form", "word__base_form"]
    ordering = ["word", "case"]
    raw_id_fields = ["word"]
    show_full_result_count = False

    class Media:
        js = ("language_trainer_app/admin/live_search.js",)


@admin.register(Context)
class ContextAdmin(admin.ModelAdmin):
    list_display = ["id", "text"]
    search_fields = ["text"]
    ordering = ["text"]


@admin.register(ContextWordFormPair)
class ContextWordFormPairAdmin(admin.ModelAdmin):
    list_display = ["id", "context", "noun_form", "adjective_form"]
    list_filter = ["noun_form__case", "noun_form__gender", "noun_form__number"]
    search_fields = ["context__text", "noun_form__word_form"]
    raw_id_fields = ["context", "noun_form", "adjective_form"]


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ["id", "phrase_start"]
    search_fields = ["phrase_start"]
    filter_horizontal = ["valid_words"]
