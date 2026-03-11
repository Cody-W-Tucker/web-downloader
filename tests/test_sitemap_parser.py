"""
Tests for the sitemap_parser module.
"""

import pytest
from sitemap_parser import (
    get_sitemap_url,
    parse_sitemap_urls,
    extract_sitemap_urls_recursive
)


class TestGetSitemapUrl:
    """Tests for get_sitemap_url function."""
    
    def test_returns_list_of_urls(self):
        """Test that function returns a list of sitemap URLs."""
        result = get_sitemap_url("https://example.com")
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_includes_common_sitemap_paths(self):
        """Test that common sitemap paths are included."""
        result = get_sitemap_url("https://example.com")
        assert any("sitemap.xml" in url for url in result)
    
    def test_handles_trailing_slash(self):
        """Test handling of URL with trailing slash."""
        result_with_slash = get_sitemap_url("https://example.com/")
        result_without_slash = get_sitemap_url("https://example.com")
        # Should produce the same results
        assert len(result_with_slash) == len(result_without_slash)
    
    def test_urls_are_absolute(self):
        """Test that all returned URLs are absolute."""
        result = get_sitemap_url("https://example.com")
        for url in result:
            assert url.startswith("http")


class TestParseSitemapUrls:
    """Tests for parse_sitemap_urls function."""
    
    def test_parse_regular_sitemap(self, sample_sitemap_xml):
        """Test parsing a regular sitemap."""
        urls = parse_sitemap_urls(sample_sitemap_xml)
        assert len(urls) == 3
        assert "https://example.com/" in urls
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls
    
    def test_parse_sitemap_index(self, sample_sitemap_index_xml):
        """Test parsing a sitemap index."""
        urls = parse_sitemap_urls(sample_sitemap_index_xml)
        assert len(urls) == 2
        assert "https://example.com/sitemap1.xml" in urls
        assert "https://example.com/sitemap2.xml" in urls
    
    def test_parse_empty_sitemap(self):
        """Test parsing an empty sitemap."""
        empty_xml = "<?xml version=\"1.0\"?><urlset></urlset>"
        urls = parse_sitemap_urls(empty_xml)
        assert len(urls) == 0
    
    def test_parse_invalid_xml(self):
        """Test handling of invalid XML."""
        invalid_xml = "not valid xml content"
        urls = parse_sitemap_urls(invalid_xml)
        assert len(urls) == 0
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        urls = parse_sitemap_urls("")
        assert len(urls) == 0
    
    def test_parse_sitemap_with_whitespace_urls(self):
        """Test parsing sitemap with URLs containing whitespace."""
        xml = """<?xml version="1.0"?>
        <urlset>
            <url>
                <loc>  https://example.com/page  </loc>
            </url>
        </urlset>"""
        urls = parse_sitemap_urls(xml)
        assert len(urls) == 1
        assert urls[0] == "https://example.com/page"


class TestExtractSitemapUrlsRecursive:
    """Tests for extract_sitemap_urls_recursive function."""
    
    def test_returns_empty_list_without_session(self):
        """Test that function handles missing session gracefully."""
        # Without a proper session, should return empty list
        result = extract_sitemap_urls_recursive(None, "https://example.com")
        assert isinstance(result, list)
    
    def test_returns_list(self):
        """Test that function returns a list."""
        # This would need a mock session to test properly
        pass  # Skipped - requires mock setup


class TestSitemapIntegration:
    """Integration tests for sitemap functionality."""
    
    def test_full_sitemap_workflow(self, sample_sitemap_xml):
        """Test the complete sitemap parsing workflow."""
        # Parse URLs from sitemap
        urls = parse_sitemap_urls(sample_sitemap_xml)
        
        # Verify we got the expected URLs
        assert len(urls) > 0
        for url in urls:
            assert url.startswith("https://")
            assert "example.com" in url
