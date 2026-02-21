from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
import csv
import io

from language_trainer_app.models.word import Word
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.case import Case
from language_trainer_app.models.word_number import WordNumber
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.context import Context
from language_trainer_app.utils.csv_import_utils import (
    validate_uploaded_file,
    find_reference_or_error,
    format_import_response,
    validate_csv_headers,
    safe_get_row_value,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_words(request):
    """
    Импорт базовых слов из CSV файла.

    Ожидаемый формат CSV:
    base_form,part_of_speech_name,gender_name
    дом,существительное,мужской
    красивый,прилагательное,мужской
    идти,глагол,
    """
    # 1. Валидация файла
    file_validation = validate_uploaded_file(request)
    if file_validation:
        return file_validation

    file = request.FILES["file"]

    try:
        # 2. Парсинг CSV
        decoded_file = file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded_file))

        # 3. Валидация заголовков
        required_headers = ["base_form", "part_of_speech_name"]
        optional_headers = ["gender_name"]
        header_validation = validate_csv_headers(
            csv_reader, required_headers, optional_headers
        )
        if header_validation:
            return header_validation

        # 4. Обработка строк
        total_rows = 0
        created_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            if not any(row.values()):  # Пропускаем пустые строки
                continue

            total_rows += 1

            try:
                # Получаем обязательные поля
                base_form = safe_get_row_value(row, "base_form", required=True)
                part_of_speech_name = safe_get_row_value(
                    row, "part_of_speech_name", required=True
                )
                gender_name = safe_get_row_value(row, "gender_name", required=False)

                # Находим PartOfSpeech по названию
                part_of_speech = find_reference_or_error(
                    PartOfSpeech,
                    "name",
                    part_of_speech_name,
                    "Invalid part_of_speech_name",
                )

                # Находим Gender по названию (если указан)
                gender = None
                if gender_name:
                    gender = find_reference_or_error(
                        Gender, "name", gender_name, "Invalid gender_name"
                    )

                # Создаем или получаем Word с помощью get_or_create (в нижнем регистре)
                word, created = Word.objects.get_or_create(
                    base_form=base_form.lower(),
                    part_of_speech=part_of_speech,
                    gender=gender,
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                if len(errors) < 20:  # Ограничение на количество ошибок
                    errors.append(f"Row {row_num}: {str(e)}")
                elif len(errors) == 20:
                    remaining_rows = (
                        sum(1 for _ in csv_reader) + 1
                    )  # +1 для текущей строки
                    errors.append(f"...and {remaining_rows} more validation errors")
                    break

        # 5. Формирование ответа
        response_data = format_import_response(
            total_rows, created_count, skipped_count, errors
        )
        return Response(response_data)

    except Exception as e:
        return Response(
            {"success": False, "error": f"CSV processing error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_contexts(request):
    """
    Импорт контекстов предложений из CSV файла.

    Ожидаемый формат CSV:
    text
    "В ____ живет моя семья"
    "Этот ____ очень ____"
    """
    # 1. Валидация файла
    file_validation = validate_uploaded_file(request)
    if file_validation:
        return file_validation

    file = request.FILES["file"]

    try:
        # 2. Парсинг CSV
        decoded_file = file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded_file))

        # 3. Валидация заголовков
        required_headers = ["text"]
        header_validation = validate_csv_headers(csv_reader, required_headers)
        if header_validation:
            return header_validation

        # 4. Обработка строк
        total_rows = 0
        created_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            if not any(row.values()):  # Пропускаем пустые строки
                continue

            total_rows += 1

            try:
                # Получаем текст контекста
                text = safe_get_row_value(row, "text", required=True)

                # Проверяем наличие хотя бы одного пропуска ____
                if "____" not in text:
                    raise ValueError("Context must contain '____' placeholder")

                # Создаем или получаем Context с помощью get_or_create (текст в нижнем регистре)
                context, created = Context.objects.get_or_create(text=text.lower())

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                if len(errors) < 20:  # Ограничение на количество ошибок
                    errors.append(f"Row {row_num}: {str(e)}")
                elif len(errors) == 20:
                    remaining_rows = (
                        sum(1 for _ in csv_reader) + 1
                    )  # +1 для текущей строки
                    errors.append(f"...and {remaining_rows} more validation errors")
                    break

        # 5. Формирование ответа
        response_data = format_import_response(
            total_rows, created_count, skipped_count, errors
        )
        return Response(response_data)

    except Exception as e:
        return Response(
            {"success": False, "error": f"CSV processing error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_word_forms(request):
    """
    Импорт форм слов из CSV файла.

    Ожидаемый формат CSV:
    word_base_form,word_part_of_speech_name,word_gender_name,word_form,case_name,form_gender_name,number_name
    дом,существительное,мужской,дом,именительный,мужской,единственное
    дом,существительное,мужской,дома,родительный,мужской,единственное
    """
    # 1. Валидация файла
    file_validation = validate_uploaded_file(request)
    if file_validation:
        return file_validation

    file = request.FILES["file"]

    try:
        # 2. Парсинг CSV
        decoded_file = file.read().decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(decoded_file))

        # 3. Валидация заголовков
        required_headers = [
            "word_base_form",
            "word_part_of_speech_name",
            "word_form",
            "case_name",
            "number_name",
        ]
        optional_headers = ["word_gender_name", "form_gender_name"]
        header_validation = validate_csv_headers(
            csv_reader, required_headers, optional_headers
        )
        if header_validation:
            return header_validation

        # 4. Обработка строк
        total_rows = 0
        created_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            if not any(row.values()):  # Пропускаем пустые строки
                continue

            total_rows += 1

            try:
                # Получаем данные для поиска базового слова
                word_base_form = safe_get_row_value(
                    row, "word_base_form", required=True
                )
                word_part_of_speech_name = safe_get_row_value(
                    row, "word_part_of_speech_name", required=True
                )
                word_gender_name = safe_get_row_value(
                    row, "word_gender_name", required=False
                )

                # Получаем данные для создания формы слова
                word_form = safe_get_row_value(row, "word_form", required=True)
                case_name = safe_get_row_value(row, "case_name", required=True)
                form_gender_name = safe_get_row_value(
                    row, "form_gender_name", required=False
                )
                number_name = safe_get_row_value(row, "number_name", required=True)

                # 1. Находим базовое слово по составному ключу
                try:
                    # Сначала находим part_of_speech (case-insensitive)
                    part_of_speech = find_reference_or_error(
                        PartOfSpeech,
                        "name",
                        word_part_of_speech_name,
                        "Invalid part_of_speech_name",
                    )

                    # Находим gender для базового слова (если указан, case-insensitive)
                    word_gender = None
                    if word_gender_name:
                        word_gender = find_reference_or_error(
                            Gender, "name", word_gender_name, "Invalid word gender_name"
                        )

                    # Находим базовое слово (case-insensitive поиск по base_form)
                    word = Word.objects.get(
                        base_form__iexact=word_base_form.lower(),
                        part_of_speech=part_of_speech,
                        gender=word_gender,
                    )
                except Word.DoesNotExist:
                    raise ValueError(
                        f"Word not found: base_form='{word_base_form}', part_of_speech='{word_part_of_speech_name}', gender='{word_gender_name or 'None'}'"
                    )
                except ValueError:
                    # Перехватываем ValueError от find_reference_or_error и пропускаем дальше
                    raise

                # 2. Находим справочные значения для формы слова
                case = find_reference_or_error(
                    Case, "name", case_name, "Invalid case_name"
                )

                number = find_reference_or_error(
                    WordNumber, "name", number_name, "Invalid number_name"
                )

                # Находим gender для формы слова (если указан)
                form_gender = None
                if form_gender_name:
                    form_gender = find_reference_or_error(
                        Gender, "name", form_gender_name, "Invalid form gender_name"
                    )

                # 3. Создаем WordForm с помощью get_or_create (word_form в нижнем регистре)
                word_form_obj, created = WordForm.objects.get_or_create(
                    word=word,
                    case=case,
                    gender=form_gender,
                    number=number,
                    word_form=word_form.lower(),
                )

                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                if len(errors) < 20:  # Ограничение на количество ошибок
                    errors.append(f"Row {row_num}: {str(e)}")
                elif len(errors) == 20:
                    remaining_rows = (
                        sum(1 for _ in csv_reader) + 1
                    )  # +1 для текущей строки
                    errors.append(f"...and {remaining_rows} more validation errors")
                    break

        # 5. Формирование ответа
        response_data = format_import_response(
            total_rows, created_count, skipped_count, errors
        )
        return Response(response_data)

    except Exception as e:
        return Response(
            {"success": False, "error": f"CSV processing error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
