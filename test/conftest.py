import pytest as pytest


@pytest.fixture
def monkeypatch_std(monkeypatch):
    monkeypatch.setattr("tweepy.Client", lambda *_: None)
    yield monkeypatch


@pytest.fixture()
def monkeypatch_emtpy_blacklist_env(monkeypatch_std):
    monkeypatch_std.setenv('BLACKLIST_USERID', '[]')
    yield monkeypatch_std


@pytest.fixture()
def monkeypatch_non_emtpy_blacklist_env(monkeypatch_std):
    monkeypatch_std.setenv('BLACKLIST_USERID', '["1"]')
    yield monkeypatch_std
