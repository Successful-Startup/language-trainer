"""
Утилитарные функции для CSV импорта.
Включает валидацию файлов, поиск справочников и обработку ошибок.
"""

from rest_framework.response import Response
from rest_framework import status


def validate_uploaded_file(request):
    """
    Валидирует загруженный CSV файл.

    Returns:
        Response с ошибкой или None если валидация прошла успешно
    """
    # 1. Проверка наличия файла
    if "file" not in request.FILES:
        return Response(
            {"success": False, "error": "No file provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    file = request.FILES["file"]

    # 2. Проверка расширения
    if not file.name.endswith(".csv"):
        return Response(
            {"success": False, "error": "File must be .csv format"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Проверка размера (10MB)
    if file.size > 10 * 1024 * 1024:
        return Response(
            {"success": False, "error": "File too large (max 10MB)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None  # Нет ошибок


def find_reference_or_error(model, name_field, value, error_prefix):
    """
    Найти справочник по названию или вернуть ошибку.

    Args:
        model: Django модель для поиска
        name_field: название поля для поиска (обычно 'name')
        value: искомое значение
        error_prefix: префикс для сообщения об ошибке

    Returns:
        Объект модели

    Raises:
        ValueError: если объект не найден
    """
    if not value:
        return None

    try:
        # Пробуем найти точное совпадение сначала
        return model.objects.get(**{name_field: value})
    except model.DoesNotExist:
        # Если точное совпадение не найдено, пробуем case-insensitive поиск
        # через перебор всех записей (для небольших справочников это приемлемо)
        all_objects = model.objects.all()
        for obj in all_objects:
            if getattr(obj, name_field).lower() == value.lower():
                return obj
        # Если ничего не найдено, поднимаем исключение
        raise ValueError(f"{error_prefix} '{value}'")


def format_import_response(total_rows, created_count, skipped_count, errors):
    """
    Форматирует ответ импорта с ограничением количества ошибок.

    Args:
        total_rows: общее количество обработанных строк
        created_count: количество созданных записей
        skipped_count: количество пропущенных (уже существующих) записей
        errors: список ошибок

    Returns:
        dict: отформатированный ответ
    """
    error_count = len(errors)

    # Ограничиваем количество ошибок в ответе (максимум 20)
    limited_errors = errors[:20] if error_count > 20 else errors

    # Если ошибок больше 20, добавляем сообщение о том, что есть еще
    if error_count > 20:
        remaining_errors = error_count - 20
        limited_errors.append(f"...and {remaining_errors} more validation errors")

    return {
        "success": error_count == 0,
        "total_rows": total_rows,
        "created": created_count,
        "skipped": skipped_count,
        "errors": error_count,
        "error_details": limited_errors,
    }


def validate_csv_headers(csv_reader, required_headers, optional_headers=None):
    """
    Валидирует наличие обязательных заголовков в CSV.

    Args:
        csv_reader: объект csv.DictReader
        required_headers: список обязательных заголовков
        optional_headers: список опциональных заголовков

    Returns:
        Response с ошибкой или None если валидация прошла успешно
    """
    if not csv_reader.fieldnames:
        return Response(
            {"success": False, "error": "CSV file has no headers"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    missing_headers = []
    for header in required_headers:
        if header not in csv_reader.fieldnames:
            missing_headers.append(header)

    if missing_headers:
        return Response(
            {"success": False, "error": f"Missing required headers: {missing_headers}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None


def safe_get_row_value(row, field_name, required=True):
    """
    Безопасно получает значение из строки CSV с проверкой на пустоту.

    Args:
        row: словарь строки CSV
        field_name: название поля
        required: обязательно ли поле

    Returns:
        str: значение поля или None

    Raises:
        ValueError: если обязательное поле пустое
    """
    value = row.get(field_name, "").strip()

    if required and not value:
        raise ValueError(f"{field_name} is required")

    return value if value else None
