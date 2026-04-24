"""
Shared fixtures for livecheck tests.
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from livecheck import Schema, Rule, RuleSet, validate, ValidationError


@pytest.fixture
def user_schema():
    return Schema({
        "email":    Rule("must be a valid email"),
        "age":      Rule("must be between 18 and 120"),
        "username": [Rule("must be a non-empty string"), Rule("must have length at least 3")],
        "role":     Rule("must be one of admin, editor, viewer"),
    })

@pytest.fixture
def valid_user():
    return {"email": "alice@example.com", "age": 25, "username": "alice", "role": "admin"}

@pytest.fixture
def invalid_user():
    return {"email": "not-an-email", "age": 200, "username": "a", "role": "superuser"}
