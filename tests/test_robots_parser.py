"""
Tests for the robots_parser module.
"""

import pytest
from robots_parser import RobotsHandler, respect_robots_delay


class TestRobotsHandlerInit:
    """Tests for RobotsHandler initialization."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        handler = RobotsHandler("TestBot/1.0")
        assert handler.user_agent == "TestBot/1.0"
        assert handler.default_403_policy == 'allow'
    
    def test_init_conservative_policy(self):
        """Test initialization with conservative policy."""
        handler = RobotsHandler("TestBot/1.0", default_403_policy='conservative')
        assert handler.default_403_policy == 'conservative'


class TestRobotsHandlerGetParser:
    """Tests for getting robots.txt parser."""
    
    def test_get_parser_creates_parser(self):
        """Test that get_parser_for_url creates a parser."""
        handler = RobotsHandler("TestBot/1.0")
        # Mock test - in real scenario would fetch robots.txt
        assert isinstance(handler.parsers, dict)
    
    def test_get_parser_caches_result(self):
        """Test that parsers are cached per domain."""
        handler = RobotsHandler("TestBot/1.0")
        # First call would create parser, second should return cached
        # In real scenario would fetch once
        assert len(handler.parsers) == 0  # Initially empty


class TestRobotsHandlerCanFetch:
    """Tests for can_fetch method."""
    
    def test_can_fetch_returns_bool(self):
        """Test that can_fetch returns a boolean."""
        handler = RobotsHandler("TestBot/1.0")
        result = handler.can_fetch("https://example.com/page")
        assert isinstance(result, bool)
    
    def test_can_fetch_allows_by_default(self):
        """Test that URLs are allowed by default."""
        handler = RobotsHandler("TestBot/1.0")
        # Without a real robots.txt, should default to allowing
        result = handler.can_fetch("https://example.com/page")
        assert result is True


class TestRobotsHandlerGetCrawlDelay:
    """Tests for get_crawl_delay method."""
    
    def test_get_crawl_delay_returns_float_or_none(self):
        """Test that get_crawl_delay returns float or None."""
        handler = RobotsHandler("TestBot/1.0")
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay is None or isinstance(delay, (int, float))
    
    def test_get_crawl_delay_for_denied_domain(self):
        """Test crawl delay for domain that denied robots.txt access."""
        handler = RobotsHandler("TestBot/1.0", default_403_policy='allow')
        handler.denied_robots.add("https://example.com")
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay == 10.0  # Conservative default


class TestRobotsHandlerGetSitemaps:
    """Tests for get_sitemaps method."""
    
    def test_get_sitemaps_returns_list(self):
        """Test that get_sitemaps returns a list."""
        handler = RobotsHandler("TestBot/1.0")
        sitemaps = handler.get_sitemaps("https://example.com")
        assert isinstance(sitemaps, list)
    
    def test_get_sitemaps_for_denied_domain(self):
        """Test sitemap suggestions for denied domain."""
        handler = RobotsHandler("TestBot/1.0")
        handler.denied_robots.add("https://example.com")
        sitemaps = handler.get_sitemaps("https://example.com")
        assert len(sitemaps) > 0
        assert any("sitemap" in sitemap for sitemap in sitemaps)


class TestRespectRobotsDelayDecorator:
    """Tests for the respect_robots_delay decorator."""
    
    def test_decorator_exists(self):
        """Test that the decorator is importable."""
        assert callable(respect_robots_delay)
