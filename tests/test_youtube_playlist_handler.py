"""
Tests for YouTube Playlist Handler
"""

import unittest
from unittest.mock import MagicMock, patch
from src.youtube_playlist_handler import YouTubePlaylistHandler


class TestYouTubePlaylistHandler(unittest.TestCase):
    """Test cases for YouTubePlaylistHandler."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"

    def test_extract_playlist_id_valid(self):
        """Test extracting playlist ID from valid URL."""
        self.handler = YouTubePlaylistHandler(self.api_key)
        url = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy5XP0QfVw7C6b8vKd2M2"
        playlist_id = self.handler.extract_playlist_id(url)
        self.assertEqual(playlist_id, "PLrAXtmRdnEQy5XP0QfVw7C6b8vKd2M2")

    def test_extract_playlist_id_invalid(self):
        """Test extracting playlist ID from invalid URL."""
        self.handler = YouTubePlaylistHandler(self.api_key)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        playlist_id = self.handler.extract_playlist_id(url)
        self.assertIsNone(playlist_id)

    def test_extract_channel_id_direct(self):
        """Test extracting channel ID from direct channel URL."""
        self.handler = YouTubePlaylistHandler(self.api_key)
        url = "https://www.youtube.com/channel/UC1234567890abcdef"
        channel_id = self.handler.extract_channel_id(url)
        self.assertEqual(channel_id, "UC1234567890abcdef")

    def test_extract_channel_id_handle(self):
        """Test extracting channel ID from handle URL."""
        self.handler = YouTubePlaylistHandler(self.api_key)
        with patch.object(
            self.handler, "_resolve_channel_id_from_handle"
        ) as mock_resolve:
            mock_resolve.return_value = "UC1234567890abcdef"

            url = "https://www.youtube.com/@TestChannel"
            channel_id = self.handler.extract_channel_id(url)
            self.assertEqual(channel_id, "UC1234567890abcdef")
            mock_resolve.assert_called_once_with("TestChannel")

    @patch("src.youtube_playlist_handler.build")
    def test_get_videos_from_playlist(self, mock_build):
        """Test getting videos from playlist."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        self.handler = YouTubePlaylistHandler(self.api_key)

        mock_response = {
            "items": [
                {
                    "snippet": {
                        "resourceId": {"videoId": "video123"},
                        "title": "Test Video",
                        "description": "Test Description",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "channelTitle": "Test Channel",
                        "thumbnails": {},
                    }
                }
            ],
            "nextPageToken": None,
        }

        mock_resource = MagicMock()
        mock_youtube.playlistItems.return_value = mock_resource
        mock_request = MagicMock()
        mock_request.execute.return_value = mock_response
        mock_resource.list.return_value = mock_request

        videos = self.handler.get_videos_from_playlist("PLtest")
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["video_id"], "video123")
        self.assertEqual(videos[0]["title"], "Test Video")

    @patch("src.youtube_playlist_handler.build")
    def test_get_videos_from_channel(self, mock_build):
        """Test getting videos from channel."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        self.handler = YouTubePlaylistHandler(self.api_key)

        mock_channels_response = {
            "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UUtest"}}}]
        }

        mock_channels_resource = MagicMock()
        mock_youtube.channels.return_value = mock_channels_resource
        mock_channels_request = MagicMock()
        mock_channels_request.execute.return_value = mock_channels_response
        mock_channels_resource.list.return_value = mock_channels_request

        with patch.object(
            self.handler, "get_videos_from_playlist"
        ) as mock_get_playlist:
            mock_get_playlist.return_value = [{"video_id": "video123"}]

            videos = self.handler.get_videos_from_channel("UCtest")
            self.assertEqual(len(videos), 1)
            self.assertEqual(videos[0]["video_id"], "video123")
            mock_get_playlist.assert_called_once_with("UUtest")

    def test_extract_video_id_watch(self):
        """Test extracting video ID from watch URL."""
        handler = YouTubePlaylistHandler(self.api_key)
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = handler.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_short(self):
        """Test extracting video ID from youtu.be short URL."""
        handler = YouTubePlaylistHandler(self.api_key)
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = handler.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_intl(self):
        """Test extracting video ID from international domain."""
        handler = YouTubePlaylistHandler(self.api_key)
        url = "https://www.youtube.de/watch?v=dQw4w9WgXcQ"
        video_id = handler.extract_video_id(url)
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_video_id_invalid(self):
        """Test invalid video ID formats."""
        handler = YouTubePlaylistHandler(self.api_key)
        urls = [
            "https://www.youtube.com/watch?v=invalid",
            "https://www.youtube.com/watch?v=a" * 10,
            "https://example.com/watch?v=dQw4w9WgXcQ",
        ]
        for url in urls:
            self.assertIsNone(handler.extract_video_id(url))

    @patch("src.youtube_playlist_handler.build")
    def test_get_video_metadata(self, mock_build):
        """Test getting single video metadata."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        handler = YouTubePlaylistHandler(self.api_key)

        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test Desc",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "channelTitle": "Test Channel",
                        "thumbnails": {"default": {"url": "thumb.jpg"}},
                    }
                }
            ]
        }
        mock_resource = MagicMock()
        mock_youtube.videos.return_value = mock_resource
        mock_request = MagicMock()
        mock_request.execute.return_value = mock_response
        mock_resource.list.return_value = mock_request

        metadata = handler.get_video_metadata("testvid123")
        self.assertEqual(metadata["video_id"], "testvid123")
        self.assertEqual(metadata["title"], "Test Video")


if __name__ == "__main__":
    unittest.main()
