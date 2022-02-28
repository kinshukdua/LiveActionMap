"""Testing Scraper Class"""
# pylint: disable=C0415
import pytest


class TestScraper:
    """Testing suite for Scraper class"""

    @staticmethod
    @pytest.mark.usefixtures("monkeypatch_emtpy_blacklist_env")
    def test_scrape_blacklist_empty():
        """Testing Scraper when blacklist is empty"""
        from scrape import Scraper
        scraper_class = Scraper('', '', '')
        assert hasattr(scraper_class, 'blacklist_usernames')
        assert isinstance(scraper_class.blacklist_usernames, list)
        assert len(scraper_class.blacklist_usernames) == 0

    @staticmethod
    @pytest.mark.usefixtures("monkeypatch_non_emtpy_blacklist_env")
    def test_scrape_blacklist_non_empty():
        """Testing scraper when blacklist is non-empty and values are casted to int"""
        from scrape import Scraper
        scraper_class = Scraper('', '', '')
        assert hasattr(scraper_class, 'blacklist_usernames')
        assert isinstance(scraper_class.blacklist_usernames, list)
        assert len(scraper_class.blacklist_usernames) > 0
        assert isinstance(scraper_class.blacklist_usernames[0], int)
        assert 1 in scraper_class.blacklist_usernames
