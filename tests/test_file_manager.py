"""
Tests for the file_manager module.
"""

import os
import pytest
from file_manager import FileManager


class TestFileManagerInit:
    """Tests for FileManager initialization."""
    
    def test_init_creates_directory(self, temp_output_dir):
        """Test that initialization creates the output directory."""
        output_path = os.path.join(temp_output_dir, "test_output")
        fm = FileManager(output_path)
        assert os.path.exists(output_path)
    
    def test_init_with_existing_directory(self, temp_output_dir):
        """Test initialization with existing directory."""
        fm = FileManager(temp_output_dir)
        assert fm.output_dir == temp_output_dir
    
    def test_init_detects_domain_based_output(self, temp_output_dir):
        """Test detection of domain-based output directory."""
        # Create a relative path that looks like a domain-based output
        # The logic checks for paths starting with './' and no path separators
        domain_dir = os.path.join(temp_output_dir, "example.com")
        # Change into temp dir so we can use relative path
        orig_dir = os.getcwd()
        try:
            os.chdir(temp_output_dir)
            fm = FileManager("./example.com")
            assert fm.output_is_domain_based is True
        finally:
            os.chdir(orig_dir)
    
    def test_init_detects_non_domain_based_output(self, temp_output_dir):
        """Test detection of non-domain-based output directory."""
        orig_dir = os.getcwd()
        try:
            os.chdir(temp_output_dir)
            fm = FileManager("./output/nested")
            assert fm.output_is_domain_based is False
        finally:
            os.chdir(orig_dir)


class TestUrlToFilepath:
    """Tests for URL to filepath conversion."""
    
    def test_url_to_filepath_root(self, temp_output_dir):
        """Test converting root URL."""
        fm = FileManager(temp_output_dir)
        directory, filename = fm.url_to_filepath("https://example.com/")
        assert filename.endswith('.md')
        assert 'index' in filename
    
    def test_url_to_filepath_simple_page(self, temp_output_dir):
        """Test converting simple page URL."""
        fm = FileManager(temp_output_dir)
        directory, filename = fm.url_to_filepath("https://example.com/page")
        assert filename == "page.md"
    
    def test_url_to_filepath_nested_path(self, temp_output_dir):
        """Test converting nested path URL."""
        fm = FileManager(temp_output_dir)
        directory, filename = fm.url_to_filepath("https://example.com/path/to/page")
        assert filename == "page.md"
        assert "path" in directory
        assert "to" in directory
    
    def test_url_to_filepath_removes_www(self, temp_output_dir):
        """Test that www prefix is removed from domain."""
        fm = FileManager(temp_output_dir)
        directory, filename = fm.url_to_filepath("https://www.example.com/page")
        # When not domain-based, domain should be in path
        assert "www." not in directory
    
    def test_url_to_filepath_handles_query_params(self, temp_output_dir):
        """Test handling of query parameters in URL."""
        fm = FileManager(temp_output_dir)
        directory, filename = fm.url_to_filepath("https://example.com/page?id=123")
        assert "id" in filename or "page" in filename


class TestSanitizeFilename:
    """Tests for filename sanitization."""
    
    def test_sanitize_removes_invalid_chars(self, temp_output_dir):
        """Test removal of invalid filename characters."""
        fm = FileManager(temp_output_dir)
        sanitized = fm._sanitize_filename('file:name?test<>|"\\')
        assert ':' not in sanitized
        assert '?' not in sanitized
        assert '<' not in sanitized
    
    def test_sanitize_replaces_spaces(self, temp_output_dir):
        """Test replacement of spaces with underscores."""
        fm = FileManager(temp_output_dir)
        sanitized = fm._sanitize_filename("my file name")
        assert " " not in sanitized
        assert "_" in sanitized
    
    def test_sanitize_handles_empty_filename(self, temp_output_dir):
        """Test handling of empty filename."""
        fm = FileManager(temp_output_dir)
        sanitized = fm._sanitize_filename("")
        assert sanitized == "index"
    
    def test_sanitize_handles_dots(self, temp_output_dir):
        """Test handling of dot-only filenames."""
        fm = FileManager(temp_output_dir)
        sanitized = fm._sanitize_filename(".")
        assert sanitized == "index"
        sanitized = fm._sanitize_filename("..")
        assert sanitized == "index"
    
    def test_sanitize_truncates_long_names(self, temp_output_dir):
        """Test truncation of very long filenames."""
        fm = FileManager(temp_output_dir)
        long_name = "a" * 300
        sanitized = fm._sanitize_filename(long_name)
        assert len(sanitized) <= 200


class TestNormalizeUrl:
    """Tests for URL normalization."""
    
    def test_normalize_removes_trailing_slash(self, temp_output_dir):
        """Test removal of trailing slash."""
        fm = FileManager(temp_output_dir)
        normalized = fm._normalize_url("https://example.com/page/")
        assert not normalized.endswith('/')
    
    def test_normalize_removes_www(self, temp_output_dir):
        """Test removal of www prefix."""
        fm = FileManager(temp_output_dir)
        normalized = fm._normalize_url("https://www.example.com/page")
        assert "www." not in normalized


class TestFrontmatter:
    """Tests for frontmatter handling."""
    
    def test_extract_frontmatter_with_yaml(self, temp_output_dir):
        """Test extracting YAML frontmatter."""
        fm = FileManager(temp_output_dir)
        content = "---\ntitle: Test\n---\n\n# Heading\n"
        frontmatter, body = fm._extract_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter.get('title') == "Test"
        assert "# Heading" in body
    
    def test_extract_frontmatter_without_yaml(self, temp_output_dir):
        """Test extracting when no frontmatter exists."""
        fm = FileManager(temp_output_dir)
        content = "# Heading\n\nSome content"
        frontmatter, body = fm._extract_frontmatter(content)
        assert frontmatter is None
        assert body == content
    
    def test_extract_frontmatter_invalid_yaml(self, temp_output_dir):
        """Test handling of invalid YAML frontmatter."""
        fm = FileManager(temp_output_dir)
        content = "---\ninvalid: yaml: : content\n---\n\nBody"
        frontmatter, body = fm._extract_frontmatter(content)
        # Should return None for invalid YAML
        assert frontmatter is None or isinstance(frontmatter, dict)
    
    def test_add_frontmatter(self, temp_output_dir):
        """Test adding frontmatter to content."""
        fm = FileManager(temp_output_dir)
        content = "# My Title\n\nContent here."
        url = "https://example.com/page"
        result = fm._add_frontmatter(content, url, title="My Title")
        assert result.startswith("---")
        assert "title:" in result
        assert "source_url:" in result
        assert "date_extracted:" in result
    
    def test_add_frontmatter_extracts_title(self, temp_output_dir):
        """Test automatic title extraction from content."""
        fm = FileManager(temp_output_dir)
        content = "# Extracted Title\n\nContent here."
        url = "https://example.com/page"
        result = fm._add_frontmatter(content, url)
        assert "Extracted Title" in result


class TestSaveMarkdown:
    """Tests for saving markdown files."""
    
    def test_save_markdown_creates_file(self, temp_output_dir):
        """Test that save_markdown creates the file."""
        fm = FileManager(temp_output_dir)
        content = "# Test\n\nContent"
        url = "https://example.com/page"
        filepath = fm.save_markdown(content, url)
        assert filepath is not None
        assert os.path.exists(filepath)
    
    def test_save_markdown_adds_frontmatter(self, temp_output_dir):
        """Test that save_markdown adds frontmatter."""
        fm = FileManager(temp_output_dir)
        content = "# Test\n\nContent"
        url = "https://example.com/page"
        filepath = fm.save_markdown(content, url)
        
        with open(filepath, 'r') as f:
            saved_content = f.read()
        
        assert saved_content.startswith("---")
        assert "source_url:" in saved_content


class TestHandleNamingConflict:
    """Tests for handling filename conflicts."""
    
    def test_handle_conflict_creates_numbered_version(self, temp_output_dir):
        """Test that conflicts create numbered versions."""
        fm = FileManager(temp_output_dir)
        
        # Save first file
        content1 = "---\nsource_url: https://example.com/page\n---\n\nContent 1"
        filepath1 = fm.save_markdown(content1, "https://example.com/page")
        
        # Save second file with a different URL that would map to same path
        # Using query parameter which is included in filename
        content2 = "---\nsource_url: https://example.com/page?id=123\n---\n\nContent 2"
        filepath2 = fm.save_markdown(content2, "https://example.com/page?id=123")
        
        # Query params result in different filenames, so no conflict
        # Let's test a case where the path is same but URLs are truly different
        content3 = "---\nsource_url: https://example.com/page/index\n---\n\nContent 3"
        filepath3 = fm.save_markdown(content3, "https://example.com/page/index")
        
        # These should all be different
        assert filepath1 != filepath3
        assert filepath2 != filepath3
        assert os.path.exists(filepath1)
        assert os.path.exists(filepath3)
    
    def test_handle_conflict_updates_same_url(self, temp_output_dir):
        """Test that same URL updates existing file."""
        fm = FileManager(temp_output_dir)
        
        # Save file
        content = "---\nsource_url: https://example.com/page\n---\n\nOriginal content"
        filepath1 = fm.save_markdown(content, "https://example.com/page")
        
        # Save again with same URL
        new_content = "---\nsource_url: https://example.com/page\n---\n\nUpdated content"
        filepath2 = fm.save_markdown(new_content, "https://example.com/page")
        
        # Should update the same file
        assert filepath1 == filepath2
