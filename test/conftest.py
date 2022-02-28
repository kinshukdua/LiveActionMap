"""ConfTest.py of test suite"""
import pytest


@pytest.fixture(name="monkeypatch_std")
def fixture_monkeypatch_std(monkeypatch):
    """Mocking tweepy Client"""
    monkeypatch.setattr("tweepy.Client", lambda *_: None)
    yield monkeypatch


@pytest.fixture()
def monkeypatch_emtpy_blacklist_env(monkeypatch_std):
    """Mocking empty blacklist_userID list"""
    monkeypatch_std.setenv('BLACKLIST_USERID', '[]')
    yield monkeypatch_std


@pytest.fixture()
def monkeypatch_non_emtpy_blacklist_env(monkeypatch_std):
    """Mocking non empty blacklist_userID list"""
    monkeypatch_std.setenv('BLACKLIST_USERID', '["1"]')
    yield monkeypatch_std
