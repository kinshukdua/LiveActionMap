def test_scrape_blacklist_empty(monkeypatch_emtpy_blacklist_env):
    from scrape import Scraper
    s = Scraper('', '', '')
    assert hasattr(s, 'blacklist_usernames')
    assert isinstance(s.blacklist_usernames, list)
    assert len(s.blacklist_usernames) == 0


def test_scrape_blacklist_non_empty(monkeypatch_non_emtpy_blacklist_env):
    from scrape import Scraper
    s = Scraper('', '', '')
    assert hasattr(s, 'blacklist_usernames')
    assert isinstance(s.blacklist_usernames, list)
    assert len(s.blacklist_usernames) > 0
    assert isinstance(s.blacklist_usernames[0], int)
    assert 1 in s.blacklist_usernames
