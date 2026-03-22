# Tech Debt

Items tracked here are known issues that were consciously deferred.
Each entry includes context so future contributors understand the tradeoff.

---

## 1. `Phrase` model — dead code in both backend and frontend

**Location (backend):** `language_trainer_app/models/phrase.py`
**Location (frontend):** `language-trainer-web/src/types/api.ts` (`Phrase` type)

**Status:** Not exposed via any API endpoint. No serializer, no viewset, no URL route.
The frontend type exists but is never fetched or rendered.

**Risk:** Low. The model only adds one extra table to the DB schema.

**Suggested action:** Remove `Phrase` from `models/__init__.py`, delete
`models/phrase.py`, drop the corresponding migration columns, and remove the
frontend type. Coordinate both sides in a single PR.

**Why not done now:** No test coverage around `Phrase`; removing it requires
a new migration (schema change) which was out of scope for this refactor.

---

## 2. `psycopg2-binary` → `psycopg2` in production

**Location:** `requirements.txt`

**Status:** `psycopg2-binary` bundles its own `libpq` and OpenSSL, which is
convenient for development but [not recommended for production](https://www.psycopg.org/docs/install.html#binary-install-from-pypi).
In production, `psycopg2` (source package) links against the system `libpq`
and avoids potential conflicts with system OpenSSL.

**Risk:** Medium in production. Fine for development.

**Suggested action:** In production Docker images, install `psycopg2` instead
of `psycopg2-binary`. This requires `libpq-dev` and `gcc` in the build stage.
A multi-stage Dockerfile would keep the final image slim.

---

## 3. `blank=True` missing on nullable FK fields

**Location:** `WordForm.gender`, `ContextWordFormPair.adjective_form`

**Status:** These fields have `null=True` but not `blank=True`. Django convention
is to set both together for optional FK fields so that form validation also
allows empty values. Currently this inconsistency is harmless because all
writes go through DRF serializers (not Django forms), but it produces
`SystemCheck` hints and can confuse future contributors using the admin.

**Suggested action:** Add `blank=True` alongside the existing `null=True` on
those fields and generate a no-op migration (Django schema changes are needed
for `blank=True` at the DB level only when combined with constraints that
reference the column).

---

## 4. API versioning

**Status:** No versioning is in place. All endpoints live under the root path
(`/words/`, `/word-forms/`, etc.).

**Risk:** Low for now — the app is a single-tenant internal tool. Would become
a concern if the API is consumed by a mobile client or a third party.

**Suggested action:** When breaking changes are needed, introduce URL-based
versioning (`/v1/words/`) using DRF's `NamespaceVersioning` or a URL prefix.
This was out of scope for the current refactor.
