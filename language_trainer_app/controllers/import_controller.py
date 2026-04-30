import csv
import io

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from language_trainer_app.models.case import Case
from language_trainer_app.models.context import Context
from language_trainer_app.models.gender import Gender
from language_trainer_app.models.part_of_speech import PartOfSpeech
from language_trainer_app.models.word import Word
from language_trainer_app.models.word_form import WordForm
from language_trainer_app.models.word_number import WordNumber
from language_trainer_app.utils.csv_import_utils import (
    MAX_ERRORS,
    find_reference_or_error,
    format_import_response,
    safe_get_row_value,
    validate_csv_headers,
    validate_uploaded_file,
)
from language_trainer_app.utils.unicode_matching import filter_queryset_casefold_exact

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_csv(file):
    """Decode an uploaded file and return a csv.DictReader.

    Uses utf-8-sig so that Excel-generated files with a BOM are handled
    transparently.
    """
    decoded = file.read().decode("utf-8-sig")
    return csv.DictReader(io.StringIO(decoded))


def _collect_errors(errors, row_num, exc):
    """Append an error message, capping the list at MAX_ERRORS entries.

    Returns True when the error cap has been reached (caller should stop
    iterating), False otherwise.
    """
    if len(errors) < MAX_ERRORS:
        errors.append(f"Row {row_num}: {exc}")
        return False
    # Cap reached on this call — add a sentinel and signal the caller to stop.
    errors.append(f"Row {row_num}: {exc}")
    return True


# Mapping of human-readable animacy names (case-insensitive) to the values
# stored in Word.animacy. Empty / missing values map to None.
_ANIMACY_NAME_TO_VALUE = {
    "одушевлённое": Word.Animacy.ANIMATE.value,
    "одушевленное": Word.Animacy.ANIMATE.value,
    "неодушевлённое": Word.Animacy.INANIMATE.value,
    "неодушевленное": Word.Animacy.INANIMATE.value,
}


def _resolve_animacy(animacy_name):
    """Map an animacy column value to a Word.animacy choice or None."""
    if not animacy_name:
        return None
    key = animacy_name.strip().casefold()
    if not key:
        return None
    if key not in _ANIMACY_NAME_TO_VALUE:
        raise ValueError(
            "Invalid animacy_name: expected 'Одушевлённое' or 'Неодушевлённое'."
        )
    return _ANIMACY_NAME_TO_VALUE[key]


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_words(request):
    """
    Bulk-import base words from a CSV file.

    Expected CSV format:
        base_form,part_of_speech_name,gender_name,animacy_name
        дом,существительное,мужской,Неодушевлённое
        собака,существительное,женский,Одушевлённое
        красивый,прилагательное,мужской,
        идти,глагол,,
    """
    file_error = validate_uploaded_file(request)
    if file_error:
        return file_error

    try:
        csv_reader = _parse_csv(request.FILES["file"])

        header_error = validate_csv_headers(
            csv_reader,
            required_headers=["base_form", "part_of_speech_name"],
            optional_headers=["gender_name", "animacy_name"],
        )
        if header_error:
            return header_error

        total_rows = created_count = skipped_count = 0
        errors = []

        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):
                if not any(row.values()):
                    continue

                total_rows += 1

                try:
                    base_form = safe_get_row_value(row, "base_form", required=True)
                    pos_name = safe_get_row_value(
                        row, "part_of_speech_name", required=True
                    )
                    gender_name = safe_get_row_value(row, "gender_name", required=False)
                    animacy_name = safe_get_row_value(
                        row, "animacy_name", required=False
                    )

                    part_of_speech = find_reference_or_error(
                        PartOfSpeech, "name", pos_name, "Invalid part_of_speech_name"
                    )
                    gender = find_reference_or_error(
                        Gender, "name", gender_name, "Invalid gender_name"
                    )
                    animacy = _resolve_animacy(animacy_name)

                    _, created = Word.objects.get_or_create(
                        base_form=base_form.lower(),
                        part_of_speech=part_of_speech,
                        gender=gender,
                        defaults={"animacy": animacy},
                    )
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1

                except Exception as exc:
                    if _collect_errors(errors, row_num, exc):
                        break

        return Response(
            format_import_response(total_rows, created_count, skipped_count, errors)
        )

    except (UnicodeDecodeError, csv.Error) as exc:
        return Response(
            {"success": False, "error": f"CSV processing error: {exc}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_contexts(request):
    """
    Bulk-import sentence contexts from a CSV file.

    Expected CSV format:
        text
        "В ____ живет моя семья"
        "Этот ____ очень ____"
    """
    file_error = validate_uploaded_file(request)
    if file_error:
        return file_error

    try:
        csv_reader = _parse_csv(request.FILES["file"])

        header_error = validate_csv_headers(csv_reader, required_headers=["text"])
        if header_error:
            return header_error

        total_rows = created_count = skipped_count = 0
        errors = []

        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):
                if not any(row.values()):
                    continue

                total_rows += 1

                try:
                    text = safe_get_row_value(row, "text", required=True)

                    if "____" not in text:
                        raise ValueError(
                            "Context must contain '____' as the blank placeholder."
                        )
                    if text.count("____") > 1:
                        raise ValueError(
                            "Context must contain exactly one '____' placeholder, found more than one."
                        )

                    _, created = Context.objects.get_or_create(text=text)
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1

                except Exception as exc:
                    if _collect_errors(errors, row_num, exc):
                        break

        return Response(
            format_import_response(total_rows, created_count, skipped_count, errors)
        )

    except (UnicodeDecodeError, csv.Error) as exc:
        return Response(
            {"success": False, "error": f"CSV processing error: {exc}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_word_forms(request):
    """
    Bulk-import word forms from a CSV file.

    Expected CSV format:
        word_base_form,word_part_of_speech_name,word_gender_name,word_form,case_name,form_gender_name,number_name
        дом,существительное,мужской,дом,именительный,мужской,единственное
        дом,существительное,мужской,дома,родительный,мужской,единственное
    """
    file_error = validate_uploaded_file(request)
    if file_error:
        return file_error

    try:
        csv_reader = _parse_csv(request.FILES["file"])

        header_error = validate_csv_headers(
            csv_reader,
            required_headers=[
                "word_base_form",
                "word_part_of_speech_name",
                "word_form",
                "case_name",
                "number_name",
            ],
            optional_headers=["word_gender_name", "form_gender_name"],
        )
        if header_error:
            return header_error

        total_rows = created_count = skipped_count = 0
        errors = []

        with transaction.atomic():
            for row_num, row in enumerate(csv_reader, start=2):
                if not any(row.values()):
                    continue

                total_rows += 1

                try:
                    word_base_form = safe_get_row_value(
                        row, "word_base_form", required=True
                    )
                    word_pos_name = safe_get_row_value(
                        row, "word_part_of_speech_name", required=True
                    )
                    word_gender_name = safe_get_row_value(
                        row, "word_gender_name", required=False
                    )
                    word_form_str = safe_get_row_value(row, "word_form", required=True)
                    case_name = safe_get_row_value(row, "case_name", required=True)
                    form_gender_name = safe_get_row_value(
                        row, "form_gender_name", required=False
                    )
                    number_name = safe_get_row_value(row, "number_name", required=True)

                    part_of_speech = find_reference_or_error(
                        PartOfSpeech,
                        "name",
                        word_pos_name,
                        "Invalid part_of_speech_name",
                    )
                    word_gender = find_reference_or_error(
                        Gender, "name", word_gender_name, "Invalid word gender_name"
                    )

                    word = filter_queryset_casefold_exact(
                        Word.objects.filter(
                            part_of_speech=part_of_speech,
                            gender=word_gender,
                        ),
                        "base_form",
                        word_base_form,
                    ).first()
                    if word is None:
                        raise ValueError(
                            f"Word not found: base_form='{word_base_form}', "
                            f"part_of_speech='{word_pos_name}', "
                            f"gender='{word_gender_name or 'None'}'"
                        )

                    case = find_reference_or_error(
                        Case, "name", case_name, "Invalid case_name"
                    )
                    number = find_reference_or_error(
                        WordNumber, "name", number_name, "Invalid number_name"
                    )
                    form_gender = find_reference_or_error(
                        Gender, "name", form_gender_name, "Invalid form gender_name"
                    )

                    _, created = WordForm.objects.get_or_create(
                        word=word,
                        case=case,
                        gender=form_gender,
                        number=number,
                        word_form=word_form_str.lower(),
                    )
                    if created:
                        created_count += 1
                    else:
                        skipped_count += 1

                except Exception as exc:
                    if _collect_errors(errors, row_num, exc):
                        break

        return Response(
            format_import_response(total_rows, created_count, skipped_count, errors)
        )

    except (UnicodeDecodeError, csv.Error) as exc:
        return Response(
            {"success": False, "error": f"CSV processing error: {exc}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
