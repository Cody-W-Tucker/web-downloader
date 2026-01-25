"""
Tests for main module functionality
"""

import unittest
from unittest.mock import MagicMock, patch
from src.main import process_url, ProcessingError


class TestMainFunctionality(unittest.TestCase):
    """Test cases for main module functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.mock_extractor = MagicMock()
        self.mock_file_manager = MagicMock()

    def test_process_url_success(self):
        """Test successful URL processing."""
        # Setup mocks
        self.mock_session.get.return_value.text = (
            "<html><body>Test content</body></html>"
        )
        self.mock_extractor.extract_content.return_value = (
            {"title": "Test"},
            "Cleaned content",
        )
        self.mock_file_manager.save_markdown.return_value = "/path/to/file.md"

        with patch("src.main.convert_html_to_markdown", return_value="# Test\nContent"):
            result = process_url(
                "http://example.com",
                self.mock_session,
                self.mock_extractor,
                self.mock_file_manager,
            )

            self.assertEqual(result, "/path/to/file.md")

    def test_process_url_empty_content(self):
        """Test processing URL with empty content."""
        self.mock_session.get.return_value.text = ""

        with self.assertRaises(ProcessingError) as cm:
            process_url(
                "http://example.com",
                self.mock_session,
                self.mock_extractor,
                self.mock_file_manager,
            )

        self.assertIn("No content", str(cm.exception))

    def test_process_url_no_extracted_content(self):
        """Test processing URL where content extraction fails."""
        self.mock_session.get.return_value.text = "<html><body>Content</body></html>"
        self.mock_extractor.extract_content.return_value = ({"title": "Test"}, None)

        with self.assertRaises(ProcessingError) as cm:
            process_url(
                "http://example.com",
                self.mock_session,
                self.mock_extractor,
                self.mock_file_manager,
            )

        self.assertIn("No content extracted", str(cm.exception))

    def test_process_url_markdown_conversion_fails(self):
        """Test processing URL where markdown conversion fails."""
        self.mock_session.get.return_value.text = "<html><body>Content</body></html>"
        self.mock_extractor.extract_content.return_value = (
            {"title": "Test"},
            "Cleaned content",
        )

        with patch("src.main.convert_html_to_markdown", return_value=""):
            with self.assertRaises(ProcessingError) as cm:
                process_url(
                    "http://example.com",
                    self.mock_session,
                    self.mock_extractor,
                    self.mock_file_manager,
                )

            self.assertIn("Failed to convert", str(cm.exception))

    def test_process_url_save_fails(self):
        """Test processing URL where file save fails."""
        self.mock_session.get.return_value.text = "<html><body>Content</body></html>"
        self.mock_extractor.extract_content.return_value = (
            {"title": "Test"},
            "Cleaned content",
        )
        self.mock_file_manager.save_markdown.return_value = None

        with patch("src.main.convert_html_to_markdown", return_value="# Test\nContent"):
            with self.assertRaises(ProcessingError) as cm:
                process_url(
                    "http://example.com",
                    self.mock_session,
                    self.mock_extractor,
                    self.mock_file_manager,
                )

            self.assertIn("Failed to save", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
