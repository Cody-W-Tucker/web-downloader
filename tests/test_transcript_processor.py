"""
Tests for TranscriptProcessor
"""

import unittest
from unittest.mock import patch, Mock
from web_downloader.transcript_processor import TranscriptProcessor


class TestTranscriptProcessor(unittest.TestCase):
    """Test cases for TranscriptProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = TranscriptProcessor()
        self.sample_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_load_transcript_success(self):
        """Test successful transcript loading."""
        self.processor.api = Mock()
        self.processor.api.fetch.return_value = [
            {"start": 0, "text": "Intro", "language": "en"},
            {"start": 5, "text": "Test content", "language": "en"},
        ]

        docs = self.processor.load_transcript(self.sample_url)

        self.processor.api.fetch.assert_called_once_with(
            "dQw4w9WgXcQ", languages=["en"]
        )
        self.assertEqual(len(docs), 1)
        self.assertIn("[0s] Intro", docs[0].page_content)
        self.assertIn("[5s] Test content", docs[0].page_content)

    def test_load_transcript_no_transcript(self):
        """Test handling no available transcript."""
        self.processor.api = Mock()
        self.processor.api.fetch.side_effect = Exception("No transcript found")
        self.processor.api.list.return_value = []

        docs = self.processor.load_transcript(self.sample_url)

        self.assertEqual(docs, [])

    def test_load_transcript_with_params(self):
        """Test loading transcript with custom parameters."""
        self.processor.api = Mock()
        self.processor.api.fetch.return_value = []

        self.processor.load_transcript(
            self.sample_url, language=["en"], translation=None
        )

        self.processor.api.fetch.assert_called_once_with(
            "dQw4w9WgXcQ", languages=["en"]
        )

    def test_format_transcript_empty(self):
        """Test formatting empty docs."""
        formatted = self.processor._format_transcript([])
        self.assertEqual(formatted, "")

    def test_format_transcript_content(self):
        """Test formatting transcript content."""
        mock_doc1 = Mock(page_content="0:00 Intro\n0:05 Point one")
        mock_doc2 = Mock(page_content="0:10 Point two")
        docs = [mock_doc1, mock_doc2]

        formatted = self.processor._format_transcript(docs)
        expected = "0:00 Intro\n0:05 Point one\n0:10 Point two"
        self.assertEqual(formatted, expected)

    def test_format_markdown_success(self):
        """Test full Markdown formatting with video info."""
        mock_doc = Mock(page_content="0:00 Test transcript")
        docs = [mock_doc]
        video_info = {
            "video_id": "test123",
            "title": "Test Video",
            "channel_title": "Test Channel",
        }

        md = self.processor.format_transcript_as_markdown(docs, video_info)

        self.assertIn("title: Test Video", md)
        self.assertIn("video_id: test123", md)
        self.assertIn("0:00 Test transcript", md)

    def test_format_markdown_no_content(self):
        """Test error when no content."""
        docs = []

        with self.assertRaises(ValueError):
            self.processor.format_transcript_as_markdown(docs)


if __name__ == "__main__":
    unittest.main()
