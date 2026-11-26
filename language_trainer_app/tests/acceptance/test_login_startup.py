"""Acceptance tests for the flows: a teacher logs in, and the app starts.

The teacher logs in with a password and gets two JWTs. The access token opens
write requests. The refresh token gets a new pair, and each refresh token works
only once. The start tests run manage.py in a new process, because the settings
read the environment only once, at import.
"""

import json
import os
import subprocess
import sys

import pytest
from django.conf import settings
from django.contrib.auth.models import User

from language_trainer_app.models.gender import Gender

LOGIN_URL = "/auth/login/"
REFRESH_URL = "/auth/refresh/"
GENDERS_URL = "/genders/"

USERNAME = "teacher"
PASSWORD = "pass1234"
BAD_CREDENTIALS = {"detail": "No active account found with the given credentials"}
BLACKLISTED = {"detail": "Token is blacklisted", "code": "token_not_valid"}
ANON_REQUESTS_PER_MINUTE = 60

SECRET_KEY_MISSING = "DJANGO_SECRET_KEY environment variable is not set."
BROWSER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
# Runs in the new process after Django is set up. It prints one JSON line.
GET_API_ROOT_AS_BROWSER = (
    "import json; from django.test import Client; "
    f"r = Client().get('/', HTTP_ACCEPT={BROWSER_ACCEPT!r}); "
    "print(json.dumps({'status': r.status_code, 'type': r['Content-Type']}))"
)


@pytest.fixture
def teacher(db):
    return User.objects.create_user(username=USERNAME, password=PASSWORD)


def log_in(api_client, password=PASSWORD, username=USERNAME):
    return api_client.post(
        LOGIN_URL, {"username": username, "password": password}, format="json"
    )


def refresh(api_client, refresh_token):
    return api_client.post(REFRESH_URL, {"refresh": refresh_token}, format="json")


def create_gender_with(api_client, access_token, name):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = api_client.post(GENDERS_URL, {"name": name}, format="json")
    api_client.credentials()
    return response


def start_app(*args, **env_changes):
    """Run manage.py in a new process. A None value removes the variable."""
    env = dict(os.environ)
    for name, value in env_changes.items():
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def get_api_root_as_browser(debug):
    result = start_app(
        "shell",
        "-c",
        GET_API_ROOT_AS_BROWSER,
        DJANGO_DEBUG=debug,
        DJANGO_ALLOWED_HOSTS="testserver",
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip().splitlines()[-1])


class TestLogin:
    def test_login_gives_tokens_and_the_access_token_opens_writes(
        self, api_client, teacher
    ):
        response = log_in(api_client)

        assert response.status_code == 200
        assert set(response.json()) == {"access", "refresh"}
        created = create_gender_with(api_client, response.json()["access"], "средний")
        assert created.status_code == 201
        assert Gender.objects.filter(name="средний").exists()

    def test_login_saves_the_last_login_time(self, api_client, teacher):
        assert teacher.last_login is None

        log_in(api_client)

        teacher.refresh_from_db()
        assert teacher.last_login is not None

    def test_wrong_password_gives_401_and_no_tokens(self, api_client, teacher):
        response = log_in(api_client, password="wrong-password")

        assert response.status_code == 401
        assert response.json() == BAD_CREDENTIALS

    def test_unknown_user_gives_the_same_401(self, api_client, teacher):
        response = log_in(api_client, username="nobody")

        assert response.status_code == 401
        assert response.json() == BAD_CREDENTIALS


class TestRefresh:
    def test_refresh_gives_a_new_pair_and_the_new_access_token_opens_writes(
        self, api_client, teacher
    ):
        tokens = log_in(api_client).json()

        response = refresh(api_client, tokens["refresh"])

        assert response.status_code == 200
        assert set(response.json()) == {"access", "refresh"}
        assert response.json()["refresh"] != tokens["refresh"]
        created = create_gender_with(api_client, response.json()["access"], "средний")
        assert created.status_code == 201

    def test_the_old_refresh_token_is_rejected_after_rotation(
        self, api_client, teacher
    ):
        old_refresh = log_in(api_client).json()["refresh"]
        new_refresh = refresh(api_client, old_refresh).json()["refresh"]

        response = refresh(api_client, old_refresh)

        assert response.status_code == 401
        assert response.json() == BLACKLISTED
        assert refresh(api_client, new_refresh).status_code == 200


class TestAnonymousLimit:
    def test_the_request_after_the_limit_gives_429_even_for_login(
        self, api_client, teacher
    ):
        for _ in range(ANON_REQUESTS_PER_MINUTE):
            assert api_client.get(GENDERS_URL).status_code == 200

        response = log_in(api_client)

        assert response.status_code == 429
        assert response.json()["detail"].startswith("Request was throttled.")
        assert int(response["Retry-After"]) > 0


class TestStartup:
    @pytest.mark.parametrize("debug", ["False", None], ids=["debug-false", "unset"])
    def test_production_start_without_secret_key_is_refused(self, debug):
        result = start_app("check", DJANGO_SECRET_KEY=None, DJANGO_DEBUG=debug)

        assert result.returncode != 0
        assert SECRET_KEY_MISSING in result.stderr

    def test_debug_start_without_secret_key_uses_the_dev_key(self):
        result = start_app("check", DJANGO_SECRET_KEY=None, DJANGO_DEBUG="True")

        assert result.returncode == 0, result.stderr

    def test_production_start_answers_a_browser_with_json_only(self):
        response = get_api_root_as_browser(debug="False")

        assert response == {"status": 200, "type": "application/json"}

    def test_debug_start_answers_a_browser_with_the_browsable_api(self):
        response = get_api_root_as_browser(debug="True")

        assert response == {"status": 200, "type": "text/html; charset=utf-8"}
