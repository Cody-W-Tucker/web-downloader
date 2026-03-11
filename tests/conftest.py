"""
Test configuration and fixtures for web-downloader test suite.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory in the system temp folder for test outputs.
    
    This ensures all test files go to /tmp (or system temp) instead of the repo.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="A test page for web-downloader">
        <meta name="author" content="Test Author">
    </head>
    <body>
        <main>
            <h1>Test Heading</h1>
            <p>This is a test paragraph with some content.</p>
            <p>Here's another paragraph with <a href="/page2">a link</a>.</p>
        </main>
        <footer>
            <p>Footer content</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_sitemap_xml():
    """Sample sitemap XML content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://example.com/</loc>
            <lastmod>2024-01-01</lastmod>
        </url>
        <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2024-01-02</lastmod>
        </url>
        <url>
            <loc>https://example.com/page2</loc>
            <lastmod>2024-01-03</lastmod>
        </url>
    </urlset>
    """


@pytest.fixture
def sample_sitemap_index_xml():
    """Sample sitemap index XML content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <sitemap>
            <loc>https://example.com/sitemap1.xml</loc>
        </sitemap>
        <sitemap>
            <loc>https://example.com/sitemap2.xml</loc>
        </sitemap>
    </sitemapindex>
    """


@pytest.fixture
def sample_robots_txt():
    """Sample robots.txt content for testing."""
    return """
User-agent: *
Allow: /
Disallow: /private/
Crawl-delay: 1

Sitemap: https://example.com/sitemap.xml
"""


@pytest.fixture
def mock_response():
    """Create a mock response object for testing."""

    class MockResponse:
        def __init__(self, text, status_code=200, headers=None):
            self.text = text
            self.status_code = status_code
            self.headers = headers or {}

    return MockResponse
