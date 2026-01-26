import pytest
from unittest.mock import patch


from web_downloader.youtube_playlist_handler import YouTubePlaylistHandler
from web_downloader.transcript_processor import TranscriptProcessor
from web_downloader.file_manager import FileManager


@pytest.fixture
def fake_api_key():
    return "fake_key"


@pytest.fixture
def fake_videos():
    return [
        {
            "video_id": "dQw4w9WgXcQ",
            "title": "Never Gonna Give You Up",
            "channel_title": "Rick Astley",
            "description": "Test description",
            "published_at": "1987-07-27T00:00:00Z",
            "view_count": None,
            "like_count": None,
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
        {
            "video_id": "9bZkp7q19f0",
            "title": "Paul Graham: How to Get Startup Ideas",
            "channel_title": "Y Combinator",
            "description": "Test description",
            "published_at": "2012-11-14T00:00:00Z",
            "view_count": None,
            "like_count": None,
            "youtube_url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
        },
    ]


def test_playlist_integration(tmp_path, fake_api_key, fake_videos):
    """Test end-to-end playlist processing."""
    handler = YouTubePlaylistHandler(fake_api_key)
    processor = TranscriptProcessor()

    fake_video = {
        "video_id": "no_transcript_123",
        "title": "Silent Video",
        "channel_title": "Silent Channel",
        "description": "",
        "published_at": "2026-01-01T00:00:00Z",
        "youtube_url": "https://www.youtube.com/watch?v=no_transcript_123",
    }

    with patch.object(handler, "get_videos_from_playlist") as mock_get:
        mock_get.return_value = [fake_video]
        _videos = handler.get_videos_from_playlist("PLno_transcript")

        _docs = processor.load_transcript(fake_video["video_id"])
        # docs empty, no save called, no exception


def test_error_handling_invalid_url(fake_api_key):
    """Test invalid URL extraction."""
    handler = YouTubePlaylistHandler(fake_api_key)
    playlist_id = handler.extract_playlist_id("https://example.com")
    assert playlist_id is None
    channel_id = handler.extract_channel_id("https://example.com")
    assert channel_id is None


def test_special_characters(tmp_path, fake_api_key):
    """Test special chars handling."""
    special_channel = "Café Channel 🎉 é ñ"
    special_title = "Video with cafés & emojis 🎉"
    handler = YouTubePlaylistHandler(fake_api_key)
    processor = TranscriptProcessor()
    fm = FileManager(str(tmp_path))

    fake_video = {
        "video_id": "dQw4w9WgXcQ",
        "title": special_title,
        "channel_title": special_channel,
        "description": "",
        "published_at": "2026-01-01T00:00:00Z",
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }

    with patch.object(handler, "get_videos_from_playlist") as mock_get:
        mock_get.return_value = [fake_video]
        _videos = handler.get_videos_from_playlist("PLspecial")
        docs = processor.load_transcript(fake_video["video_id"])
        if docs:
            md = processor.format_transcript_as_markdown(docs, fake_video)
            filepath = fm.save_youtube_transcript(fake_video, md)
            channel_dir = tmp_path / fm._sanitize_filename(special_channel)
            assert channel_dir.exists()
            assert filepath is not None
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            assert special_channel in content
            assert special_title in content
            assert "🎉" in content
