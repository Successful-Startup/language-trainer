# 📋 Инструкции по тестированию CSV импорта

## 🚀 Эндпоинты для тестирования

### 1. POST /api/import/words/
**URL:** `http://localhost:8000/api/import/words/`
**Файл:** `test_data/words_test.csv`
**Content-Type:** `multipart/form-data`
**Параметр:** `file`

**Ожидаемый результат:**
- 4 успешно созданных записи (дом, машина, красивый, идти/быстро если есть соответствующие части речи)
- 2-3 ошибки валидации

### 2. POST /api/import/contexts/ 
**URL:** `http://localhost:8000/api/import/contexts/`
**Файл:** `test_data/contexts_test.csv`

**Ожидаемый результат:**
- 3 успешно созданных контекста
- 1 ошибка (без пропуска ____)
- 1 пустая строка пропущена

### 3. POST /api/import/word-forms/
**URL:** `http://localhost:8000/api/import/word-forms/`  
**Файл:** `test_data/word_forms_test.csv`

**Требует предварительно:**
1. Создать слово "дом" через /api/import/words/
2. Убедиться что есть падежи и числа в БД

**Ожидаемый результат:**
- 2 успешно созданных формы слова
- 2 ошибки валидации

## 🧪 Примеры cURL команд

```bash
# Импорт слов
curl -X POST http://localhost:8000/api/import/words/ \
  -F "file=@test_data/words_test.csv"

# Импорт контекстов  
curl -X POST http://localhost:8000/api/import/contexts/ \
  -F "file=@test_data/contexts_test.csv"

# Импорт форм слов
curl -X POST http://localhost:8000/api/import/word-forms/ \
  -F "file=@test_data/word_forms_test.csv"
```

## 📊 Ожидаемые форматы ответов

### Успешный импорт:
```json
{
    "success": true,
    "total_rows": 7,
    "created": 4,
    "skipped": 1,
    "errors": 2,
    "error_details": [
        "Row 6: part_of_speech_name is required",
        "Row 7: Invalid gender_name 'неизвестный_род'"
    ]
}
```

### Ошибка файла:
```json
{
    "success": false,
    "error": "Missing required headers: ['base_form']"
}
```

## 🔍 Проверка результатов

После импорта можно проверить созданные данные:
- GET /words - список слов
- GET /contexts - список контекстов  
- GET /wordForms - список форм слов
