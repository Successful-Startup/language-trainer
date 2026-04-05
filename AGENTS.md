# language-trainer — Backend

Django REST API for the Language Trainer application.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.0 + Django REST Framework 3.15 |
| Database | PostgreSQL 16 |
| Auth | JWT via `djangorestframework-simplejwt` |
| CORS | `django-cors-headers` |
| Containerization | Docker + docker-compose |
| CI | GitHub Actions (Black formatter check + security workflow with pip-audit, pip check, deploy checks, pytest) |

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

**Architecture pattern:** `ViewSet → (Service) → Model`
ViewSets handle HTTP concerns only (request parsing, permission checking, response serialization). Business logic is extracted into a service only when it is non-trivial (e.g. `TestGeneratorService`). Simple CRUD ViewSets interact with models directly — there is no mandatory service layer for every resource.

---

## Running Locally

### Option 1: Docker (recommended)

```bash
docker-compose up
```

This starts two containers: the Django app on port `8000` and PostgreSQL on port `5432`.

When bumping PostgreSQL to a new major version for local development, do not try to reuse the existing Docker data directory. The supported workflow in this repo is:
1. Stop the stack and remove the `pgdata` Docker volume.
2. Start the new PostgreSQL container so it creates a fresh empty cluster.
3. Run `python manage.py migrate`.
4. Run `python manage.py seed_vocabulary` to repopulate reproducible vocabulary data.

This project can rebuild its baseline local data from migrations plus `seed_vocabulary`, but any hand-entered local records that are not reproducible from those sources must be exported separately before deleting the volume.

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

| Resource | Path prefix | Permissions | Search support |
|---|---|---|---|
| Words | `/words/` | Read-only for all; write requires auth | `?search=` partial search on `base_form`; `match=exact` switches to case-insensitive exact search; `part_of_speech=` narrows results |
| Genders | `/genders/` | Read-only for all; write requires auth | — |
| Cases | `/cases/` | Read-only for all; write requires auth | — |
| Parts of speech | `/parts-of-speech/` | Read-only for all; write requires auth | — |
| Word numbers | `/word-numbers/` | Read-only for all; write requires auth | — |
| Word forms | `/word-forms/` | `IsAuthenticatedOrReadOnly` | `?search=` partial search on `word_form` and `word__base_form`; `match=exact` switches to case-insensitive exact search on `word_form` (default) or `word__base_form` (with `search_field=base_form`); `word_part_of_speech=` narrows results |
| Contexts | `/contexts/` | Read-only for all; write requires auth | — |
| Context-word-form pairs | `/context-word-form-pairs/` | `IsAuthenticatedOrReadOnly` | — |

`WordViewSet` and `WordFormViewSet` both use DRF's `SearchFilter` (`filter_backends = [filters.SearchFilter]`). Passing `?search=term` performs a case-insensitive `icontains` match across all listed search fields by default.

For teacher-facing exact lookup flows, both endpoints also support an opt-in exact mode:
- `/words/?search=<term>&match=exact` → case-insensitive exact match on `base_form`
- `/word-forms/?search=<term>&match=exact` → case-insensitive exact match on `word_form`
- `/word-forms/?search=<term>&match=exact&search_field=base_form` → case-insensitive exact match on `word__base_form` (returns all declined forms of a base word)
- `/words/?part_of_speech=<id>` and `/word-forms/?word_part_of_speech=<id>` can be combined with either search mode to narrow results before serialization

The exact mode exists to power frontend dropdowns that must avoid partial matches while keeping the older partial-search behavior available for broader list filtering.

Exact-match lookups for `/words/`, `/word-forms/`, and CSV reference/import helpers are implemented with a shared Unicode-aware Python `casefold()` helper instead of relying only on DB-level `__iexact`. This avoids SQLite-specific failures for Cyrillic case-insensitive matching during local validation and CI while preserving the same behavior in PostgreSQL.

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
| `TestGeneratorService` | Generates `TestItem` instances from `TestParameters` using random sampling via `ORDER BY RANDOM()`. When `use_adjective=False`, all pairs are included regardless of whether they have an adjective form (the adjective is simply ignored in the hint/answer). When `use_adjective=True`, filters for pairs with adjective forms matching the selected cases and numbers (gender is filtered only on the noun — adjective Words don't have inherent word-level gender). The hint shows the adjective in nominative case matching the noun's word-level gender and number (uses `pair.noun_form.word.gender` as source of truth). |

---

## JWT Configuration

## Dependency And Security Workflow

- Runtime dependency pins live in `requirements.txt`; development tools live in `requirements-dev.txt`.
- The application Docker image now installs only `requirements.txt`, so dev-only packages like `black` are not shipped in the runtime container.
- The backend repo now has a dedicated `.github/workflows/security.yml` workflow that runs `pip-audit`, `pip check`, `python manage.py check --deploy`, and `pytest` on every push and pull request.
- Local validation after dependency changes should cover both dependency health and behavior: `pip check`, `pytest`, and at least one `manage.py check --deploy` run.

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

## Django Admin

Django admin is available at `http://localhost:8000/admin/`. It is a **separate server-side rendered interface** built into Django — not React, not part of `language-trainer-web`.

**Who uses it:** developers and superusers for database inspection, debugging, and operations not yet covered by TeacherPage.

**Registered models and their admin configuration:**

| Model | search_fields | list_filter | Notes |
|---|---|---|---|
| `Word` | `base_form` | `gender`, `part_of_speech` | `show_full_result_count = False`; live search JS |
| `WordForm` | `word_form`, `word__base_form` | `case`, `gender`, `number` | `show_full_result_count = False`; `raw_id_fields = ["word"]`; live search JS |
| `Context` | `text` | — | |
| `ContextWordFormPair` | `context__text`, `noun_form__word_form` | `noun_form__case`, `noun_form__gender`, `noun_form__number` | `raw_id_fields` for all FKs |
| `Phrase` | `phrase_start` | — | `filter_horizontal = ["valid_words"]` |
| `Gender`, `Case`, `PartOfSpeech`, `WordNumber` | `name` | — | Lookup tables |

**Live search:** `WordAdmin` and `WordFormAdmin` include a custom debounced JS (`language_trainer_app/static/language_trainer_app/admin/live_search.js`) that auto-submits the search form 450 ms after the user stops typing.

**Coexistence with TeacherPage:** both interfaces manage the same data independently. See `language-trainer-web/AGENTS.md` → Known Issues for the current state of TeacherPage coverage.

---

## Code Conventions

- **Formatter:** [Black](https://black.readthedocs.io/) — enforced in CI via GitHub Actions
- All new code must pass Black formatting before merging
- Run locally: `black .`

---

## Testing Approach — TDD

**Always follow Test-Driven Development (Red → Green → Refactor):**

1. Write a failing test first
2. Write the minimum code to make it pass
3. Refactor while keeping tests green

**Test runner:** Django's built-in `TestCase` + `pytest-django` (if available)

```bash
python manage.py test
# or
pytest
```

**What to test:**

| Layer | What to test |
|---|---|
| Services | All business logic (e.g. `TestGeneratorService`) — unit tests with mocked DB or `TestCase` |
| ViewSets | API endpoints — use `APIClient` to assert status codes, response shapes, and auth rules |
| Models | Custom `save()`, `clean()`, constraints, and any model methods |
| Utils | CSV import logic — use in-memory CSV files |

**Rules:**
- Every new service method must have a test written before implementation
- Every new API endpoint must have at least one happy-path and one error-path test
- Do not commit code that reduces test coverage
