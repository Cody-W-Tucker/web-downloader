"""
Tests for TranscriptProcessor
"""
import unittest
from unittest.mock import patch, Mock
from src.transcript_processor import TranscriptProcessor


class TestTranscriptProcessor(unittest.TestCase):
    """Test cases for TranscriptProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = TranscriptProcessor()
        self.sample_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    @patch('src.transcript_processor.YoutubeLoader')
    def test_load_transcript_success(self, mock_loader_class):
        """Test successful transcript loading."""
        mock_loader = Mock()
        mock_docs = [Mock(page_content="0:00 Intro\n0:05 Test content")]
        mock_loader.load.return_value = mock_docs
        mock_loader_class.from_youtube_url.return_value = mock_loader
        
        docs = self.processor.load_transcript(self.sample_url)
        
        mock_loader_class.from_youtube_url.assert_called_once_with(
            self.sample_url, language=["en"], translation=None, add_video_info=True
        )
        mock_loader.load.assert_called_once()
        self.assertEqual(docs, mock_docs)
    
    @patch('src.transcript_processor.YoutubeLoader')
    def test_load_transcript_no_transcript(self, mock_loader_class):
        """Test handling no available transcript."""
        mock_loader_class.from_youtube_url.side_effect = Exception("No transcript found")
        
        docs = self.processor.load_transcript(self.sample_url)
        
        self.assertEqual(docs, [])
    
    @patch('src.transcript_processor.YoutubeLoader')
    def test_load_transcript_languages_translation(self, mock_loader_class):
        """Test language preferences and translation."""
        mock_loader = Mock()
        mock_loader.load.return_value = []
        mock_loader_class.from_youtube_url.return_value = mock_loader
        
        self.processor.load_transcript(
            self.sample_url, 
            language=["es", "en"], 
            translation="fr"
        )
        
        mock_loader_class.from_youtube_url.assert_called_once_with(
            self.sample_url, 
            language=["es", "en"], 
            translation="fr", 
            add_video_info=True
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
            'video_id': 'test123',
            'title': 'Test Video',
            'channel_title': 'Test Channel'
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


if __name__ == '__main__':
    unittest.main()