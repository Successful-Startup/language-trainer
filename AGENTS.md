# language-trainer — Backend

Django REST API for the Language Trainer application.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.0 + Django REST Framework 3.15 |
| Database | PostgreSQL 12 |
| Auth | JWT via `djangorestframework-simplejwt` |
| CORS | `django-cors-headers` |
| Containerization | Docker + docker-compose |
| CI | GitHub Actions (Black code formatter check) |

---

## Project Structure

```
language-trainer/
├── language_trainer_project/   # Django project config (settings, root urls)
├── language_trainer_app/       # Main application
│   ├── controllers/            # DRF ViewSets (one per resource)
│   ├── models/                 # Django ORM models + dataclasses (DTOs)
│   ├── serializers/            # DRF serializers (one per model)
│   ├── services/               # Business logic layer
│   ├── urls/                   # URL router configuration
│   ├── utils/                  # CSV import utilities
│   └── migrations/             # Database migrations
├── test_data/                  # Sample CSV files for import
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── .env.example
```

**Architecture pattern:** `ViewSet → Service → Model`
Business logic lives exclusively in services. ViewSets handle HTTP concerns only (request parsing, permission checking, response serialization). Never put business logic directly in ViewSets.

---

## Running Locally

### Option 1: Docker (recommended)

```bash
docker-compose up
```

This starts two containers: the Django app on port `8000` and PostgreSQL on port `5432`.

### Option 2: Manual (venv)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env with your values
python manage.py migrate
python manage.py runserver
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure fallback | Django secret key — **must be set in production** |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hosts |
| `FRONTEND_URL` | `http://localhost:3000` | Used for CORS allowed origins (not in `.env.example` — has a default) |
| `DB_DRIVER` | `django.db.backends.postgresql` | Database backend |
| `PG_DB` | `LanguageTrainerDb` | PostgreSQL database name |
| `PG_USER` | `postgres` | PostgreSQL user |
| `PG_PASSWORD` | `postgres` | PostgreSQL password |
| `PG_HOST` | `localhost` | PostgreSQL host (`languagetrainerdb` inside Docker) |
| `PG_PORT` | `5432` | PostgreSQL port |

---

## API Endpoints

### Authentication

| Method | Path | Description | Auth required |
|---|---|---|---|
| `POST` | `/auth/login/` | Obtain access + refresh JWT tokens | No |
| `POST` | `/auth/refresh/` | Refresh access token | No (refresh token in body) |

### Resources (standard CRUD)

Each resource provides `GET /`, `POST /`, `GET /{id}/`, `PUT /{id}/`, `PATCH /{id}/`, `DELETE /{id}/`.

| Resource | Path prefix | Permissions |
|---|---|---|
| Words | `/words/` | Read-only for all; write requires auth |
| Genders | `/genders/` | Read-only for all; write requires auth |
| Cases | `/cases/` | Read-only for all; write requires auth |
| Parts of speech | `/parts-of-speech/` | Read-only for all; write requires auth |
| Word numbers | `/word-numbers/` | Read-only for all; write requires auth |
| Word forms | `/word-forms/` | `IsAuthenticatedOrReadOnly` |
| Contexts | `/contexts/` | Read-only for all; write requires auth |
| Context-word-form pairs | `/context-word-form-pairs/` | `IsAuthenticatedOrReadOnly` |

### Test generation

| Method | Path | Description | Auth required |
|---|---|---|---|
| `POST` | `/tests/generate/` | Generate up to 10 test items based on parameters | No |

Request body:
```json
{
  "use_adjective": true,
  "genders": [1, 2],
  "cases": [3, 4],
  "numbers": [1]
}
```

### CSV Import

| Method | Path | Description | Auth required |
|---|---|---|---|
| `POST` | `/api/import/words/` | Bulk import words from CSV | Yes |
| `POST` | `/api/import/contexts/` | Bulk import contexts from CSV | Yes |
| `POST` | `/api/import/word-forms/` | Bulk import word forms from CSV | Yes |

All import endpoints accept `multipart/form-data` with a `file` field.

---

## Data Models

### Entity Relationships

```
Gender ←── Word ──→ PartOfSpeech
              │
              ▼
          WordForm ──→ Case
          WordForm ──→ Gender (form gender, e.g. for adjectives)
          WordForm ──→ WordNumber
              │
              ▼
  ContextWordFormPair ──→ Context
  ContextWordFormPair ──→ WordForm (noun_form)
  ContextWordFormPair ──→ WordForm (adjective_form, optional)

Phrase ──▶ Word (M2M: valid_words)
```

### DB Models

**`Gender`** — grammatical gender (e.g. masculine, feminine, neuter)
- `name` (CharField, unique)

**`PartOfSpeech`** — part of speech (e.g. noun, adjective)
- `name` (CharField, unique)

**`WordNumber`** — grammatical number (e.g. singular, plural)
- `name` (CharField, unique)

**`Case`** — grammatical case (e.g. nominative, genitive)
- `name` (CharField, unique)

**`Word`** — a word in its base (dictionary) form
- `base_form` (CharField, indexed)
- `gender` → FK to `Gender` (nullable)
- `part_of_speech` → FK to `PartOfSpeech`
- Unique constraint: `(base_form, part_of_speech, gender)`

**`WordForm`** — a specific declined/inflected form of a word
- `word` → FK to `Word`
- `case` → FK to `Case`
- `gender` → FK to `Gender` (nullable — form-level gender, e.g. for adjectives)
- `number` → FK to `WordNumber`
- `word_form` (CharField — the actual declined string)
- Unique constraint: `(word, case, gender, number)`

**`Context`** — a sentence fragment used in tests (must contain `____` placeholder)
- `text` (CharField, unique)

**`ContextWordFormPair`** — links a context to a noun form and an optional adjective form; these are the test items
- `context` → FK to `Context`
- `noun_form` → FK to `WordForm`
- `adjective_form` → FK to `WordForm` (nullable)
- Unique constraint: `(context, adjective_form, noun_form)`

**`Phrase`** — a phrase with a set of valid words (currently not exposed via API)
- `phrase_start` (CharField)
- `valid_words` → M2M to `Word`

### DTOs (Python dataclasses, not stored in DB)

**`TestParameters`** — input for test generation
- `use_adjective: bool`
- `genders: List[int]`
- `cases: List[int]`
- `numbers: List[int]`

**`TestItem`** — a single generated test question
- `context: str` — sentence with `____` placeholder
- `noun_with_adjective: str` — hint shown to the student (e.g. "красивая машина")
- `correct_answer: str` — the correct declined form

---

## Services

| Service | Responsibility |
|---|---|
| `WordService` | CRUD for `Word` |
| `WordFormService` | CRUD for `WordForm` |
| `ContextService` | CRUD for `Context` |
| `ContextWordFormPairService` | CRUD for `ContextWordFormPair`; `get_by_params()` filters pairs by gender/case/number |
| `TestGeneratorService` | Generates `TestItem` instances from `TestParameters` using random sampling |

---

## JWT Configuration

| Setting | Value |
|---|---|
| Access token lifetime | 60 minutes |
| Refresh token lifetime | 7 days |
| Rotate refresh tokens | Yes |
| Blacklist after rotation | Yes |
| Auth header | `Authorization: Bearer <token>` |

---

## CSV Import Format

### Words (`/api/import/words/`)

| Column | Required | Description |
|---|---|---|
| `base_form` | Yes | Dictionary form of the word |
| `part_of_speech_name` | Yes | Must match an existing `PartOfSpeech.name` |
| `gender_name` | No | Must match an existing `Gender.name` if provided |

### Contexts (`/api/import/contexts/`)

| Column | Required | Description |
|---|---|---|
| `text` | Yes | Sentence fragment; must contain `____` as the blank placeholder |

### Word Forms (`/api/import/word-forms/`)

| Column | Required | Description |
|---|---|---|
| `word_base_form` | Yes | Base form of the parent word |
| `word_part_of_speech_name` | Yes | Part of speech of the parent word |
| `word_gender_name` | No | Gender of the parent word |
| `word_form` | Yes | The declined form string |
| `case_name` | Yes | Must match an existing `Case.name` |
| `form_gender_name` | No | Form-level gender (e.g. for adjectives) |
| `number_name` | Yes | Must match an existing `WordNumber.name` |

Import behavior: uses `get_or_create`; skips duplicates; reports up to 20 errors before truncating.

---

## Code Conventions

- **Formatter:** [Black](https://black.readthedocs.io/) — enforced in CI via GitHub Actions
- All new code must pass Black formatting before merging
- Run locally: `black .`
