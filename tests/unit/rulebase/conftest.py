"""Shared fixtures for rulebase tests."""

import sys
from pathlib import Path

import pytest

# Make the builders importable without turning tests/ into a package.
sys.path.insert(0, str(Path(__file__).parent))

from rulebase_builders import TODAY

from knowledge.rulebase.findings import Report
from knowledge.rulebase.loader import RulebasePaths
from knowledge.rulebase.validator import validate_rulebase


def validate(paths: RulebasePaths) -> Report:
    return validate_rulebase(paths, today=TODAY)


@pytest.fixture
def check():
    return validate
