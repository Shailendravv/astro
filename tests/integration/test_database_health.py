"""Health check against a real PostgreSQL (CI service container or a local throwaway container).

Set TEST_DATABASE_URL to run; without it these tests are skipped, so a plain `pytest` never needs a
database. The URL is only ever read from the environment and is never logged.
"""

import os

import pytest

from jyotish_api.main import make_database_check

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(DATABASE_URL is None, reason="TEST_DATABASE_URL is not set")
def test_database_check_succeeds_against_a_live_database() -> None:
    assert DATABASE_URL is not None
    assert make_database_check(DATABASE_URL)() is True


def test_database_check_reports_failure_instead_of_raising() -> None:
    # Nothing listens on port 1: the check must return False, not raise or leak the URL.
    unreachable = "postgresql+psycopg://nobody:nopass@127.0.0.1:1/none"
    assert make_database_check(unreachable)() is False
