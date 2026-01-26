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

    @patch("youtube_transcript_api._api.YouTubeTranscriptApi.get_transcript")
    def test_load_transcript_success(self, mock_get_transcript):
        """Test successful transcript loading."""
        mock_get_transcript.return_value = [
            {"start": 0, "text": "Intro"},
            {"start": 5, "text": "Test content"},
        ]

        docs = self.processor.load_transcript(self.sample_url)

        mock_get_transcript.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])
        self.assertEqual(len(docs), 1)
        self.assertIn("[0s] Intro", docs[0].page_content)
        self.assertIn("[5s] Test content", docs[0].page_content)

    @patch("youtube_transcript_api._api.YouTubeTranscriptApi.get_transcript")
    def test_load_transcript_no_transcript(self, mock_get_transcript):
        """Test handling no available transcript."""
        mock_get_transcript.side_effect = Exception("No transcript found")

        docs = self.processor.load_transcript(self.sample_url)

        self.assertEqual(docs, [])

    @patch("youtube_transcript_api._api.YouTubeTranscriptApi.get_transcript")
    def test_load_transcript_with_params(self, mock_get_transcript):
        """Test loading transcript with custom parameters."""
        mock_get_transcript.return_value = []

        self.processor.load_transcript(
            self.sample_url, language=["en"], translation=None
        )

        mock_get_transcript.assert_called_once_with("dQw4w9WgXcQ", languages=["en"])

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
