"""
Tests for the crawler module.
"""

import pytest
from crawler import (
    RateLimitedSession,
    WebCrawler,
    normalize_url,
    is_internal_url,
    is_valid_url
)


class TestNormalizeUrl:
    """Tests for normalize_url function."""
    
    def test_normalize_absolute_url(self):
        """Test normalizing an already absolute URL."""
        result = normalize_url("https://example.com", "https://example.com/page")
        assert result == "https://example.com/page"
    
    def test_normalize_relative_url(self):
        """Test normalizing a relative URL."""
        result = normalize_url("https://example.com", "/page")
        assert result == "https://example.com/page"
    
    def test_normalize_relative_url_without_slash(self):
        """Test normalizing a relative URL without leading slash."""
        result = normalize_url("https://example.com/path/", "page")
        assert result == "https://example.com/path/page"
    
    def test_normalize_removes_fragment(self):
        """Test that URL fragments are removed."""
        result = normalize_url("https://example.com", "/page#section")
        assert result == "https://example.com/page"
    
    def test_normalize_keeps_query_params_for_content_pages(self):
        """Test that query params are kept for content pages."""
        result = normalize_url("https://example.com", "/page.html?id=123")
        assert "id=123" in result


class TestIsInternalUrl:
    """Tests for is_internal_url function."""
    
    def test_internal_absolute_url(self):
        """Test detecting internal absolute URL."""
        assert is_internal_url("https://example.com", "https://example.com/page") is True
    
    def test_internal_relative_url(self):
        """Test detecting internal relative URL."""
        assert is_internal_url("https://example.com", "/page") is True
    
    def test_external_url(self):
        """Test detecting external URL."""
        assert is_internal_url("https://example.com", "https://other.com/page") is False
    
    def test_external_subdomain(self):
        """Test that subdomains are treated as external."""
        assert is_internal_url("https://example.com", "https://sub.example.com/page") is False


class TestIsValidUrl:
    """Tests for is_valid_url function."""
    
    def test_valid_http_url(self):
        """Test validating HTTP URL."""
        assert is_valid_url("http://example.com/page") is True
    
    def test_valid_https_url(self):
        """Test validating HTTPS URL."""
        assert is_valid_url("https://example.com/page") is True
    
    def test_invalid_ftp_url(self):
        """Test rejecting FTP URL."""
        assert is_valid_url("ftp://example.com/file") is False
    
    def test_invalid_mailto_url(self):
        """Test rejecting mailto URL."""
        assert is_valid_url("mailto:test@example.com") is False
    
    def test_invalid_image_url(self):
        """Test rejecting image URL."""
        assert is_valid_url("https://example.com/image.jpg") is False
    
    def test_invalid_pdf_url(self):
        """Test rejecting PDF URL."""
        assert is_valid_url("https://example.com/document.pdf") is False


class TestRateLimitedSession:
    """Tests for RateLimitedSession class."""
    
    def test_init_default_user_agent(self):
        """Test initialization with default user agent."""
        session = RateLimitedSession()
        assert session.user_agent is not None
        assert len(session.user_agent) > 0
    
    def test_init_custom_user_agent(self):
        """Test initialization with custom user agent."""
        custom_ua = "TestBot/1.0"
        session = RateLimitedSession(user_agent=custom_ua)
        assert session.user_agent == custom_ua
    
    def test_init_with_delay(self):
        """Test initialization with custom delay."""
        session = RateLimitedSession(delay=2.0)
        assert session.delay == 2.0
    
    def test_init_respect_robots_enabled(self):
        """Test that robots handler is created when respect_robots is True."""
        session = RateLimitedSession(respect_robots=True)
        assert hasattr(session, 'robots_handler')
    
    def test_get_domain(self):
        """Test domain extraction from URL."""
        session = RateLimitedSession()
        domain = session._get_domain("https://example.com/path")
        assert domain == "example.com"


class TestWebCrawler:
    """Tests for WebCrawler class."""
    
    def test_init(self):
        """Test crawler initialization."""
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session, max_depth=3)
        assert crawler.base_url == "https://example.com"
        assert crawler.max_depth == 3
        assert crawler.session == session
        assert len(crawler.visited_urls) == 0
    
    def test_extract_links_from_html(self, sample_html):
        """Test link extraction from HTML."""
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session)
        links = crawler.extract_links("https://example.com", sample_html)
        assert len(links) == 1
        assert "https://example.com/page2" in links
    
    def test_extract_links_empty_html(self):
        """Test link extraction from empty HTML."""
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session)
        links = crawler.extract_links("https://example.com", "")
        assert len(links) == 0
    
    def test_extract_links_no_links(self):
        """Test link extraction from HTML without links."""
        html = "<html><body><p>No links here</p></body></html>"
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session)
        links = crawler.extract_links("https://example.com", html)
        assert len(links) == 0
    
    def test_extract_links_skips_javascript(self):
        """Test that javascript: links are skipped."""
        html = '<html><body><a href="javascript:void(0)">Click</a></body></html>'
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session)
        links = crawler.extract_links("https://example.com", html)
        assert len(links) == 0
    
    def test_extract_links_skips_anchors(self):
        """Test that anchor links are skipped."""
        html = '<html><body><a href="#section">Jump</a></body></html>'
        session = RateLimitedSession()
        crawler = WebCrawler("https://example.com", session)
        links = crawler.extract_links("https://example.com", html)
        assert len(links) == 0
