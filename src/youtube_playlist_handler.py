"""
YouTube Playlist and Channel Handler

This module provides functionality to extract YouTube playlist and channel IDs from URLs,
and retrieve video information using the YouTube Data API v3.
"""

import logging
import re
import json
import time
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubePlaylistHandler:
    """
    Handler for extracting YouTube playlist and channel video information.
    
    Supports various YouTube URL formats for playlists and channels.
    Uses YouTube Data API v3 for retrieving video metadata.
    """
    
    def __init__(self, api_key):
        """
        Initialize the handler with YouTube Data API key.
        
        Args:
            api_key (str): YouTube Data API v3 key
        """
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.logger = logging.getLogger(__name__)
    
    def extract_playlist_id(self, url):
        """
        Extract playlist ID from YouTube playlist URL.
        
        Args:
            url (str): YouTube playlist URL
            
        Returns:
            str or None: Playlist ID if found, None otherwise
        """
        try:
            parsed = urlparse(url)
            if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
                query = parse_qs(parsed.query)
                if 'list' in query:
                    playlist_id = query['list'][0]
                    # Validate playlist ID format (starts with PL, RD, etc.)
                    if re.match(r'^(PL|RD|LL|UU|FL|OL)[A-Za-z0-9_-]+$', playlist_id):
                        return playlist_id
        except Exception as e:
            self.logger.warning(f"Error extracting playlist ID from {url}: {e}")
        
        return None
    
    def extract_channel_id(self, url):
        """
        Extract or resolve channel ID from various YouTube channel URL formats.
        
        Args:
            url (str): YouTube channel URL
            
        Returns:
            str or None: Channel ID if found, None otherwise
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Direct channel ID: /channel/UC...
            if '/channel/' in path:
                channel_id = path.split('/channel/')[1].split('/')[0]
                if re.match(r'^UC[A-Za-z0-9_-]+$', channel_id):
                    return channel_id
            
            # Handle (@username)
            elif '/@' in path:
                handle = path.split('/@')[1].split('/')[0]
                return self._resolve_channel_id_from_handle(handle)
            
            # Legacy user URL: /user/username
            elif '/user/' in path:
                username = path.split('/user/')[1].split('/')[0]
                return self._resolve_channel_id_from_username(username)
            
            # Custom URL: /c/channelname (may not resolve reliably)
            elif '/c/' in path:
                custom_name = path.split('/c/')[1].split('/')[0]
                # Try as handle first
                channel_id = self._resolve_channel_id_from_handle(custom_name)
                if channel_id:
                    return channel_id
                # Could implement search fallback, but keeping simple for now
        
        except Exception as e:
            self.logger.warning(f"Error extracting channel ID from {url}: {e}")
        
        return None
    
    def _resolve_channel_id_from_handle(self, handle):
        """
        Resolve channel ID from handle using YouTube API.
        
        Args:
            handle (str): YouTube handle (without @)
            
        Returns:
            str or None: Channel ID if found
        """
        try:
            request = self.youtube.channels().list(
                part='id',
                forHandle=handle
            )
            response = self._execute_with_retry(request)
            
            if 'items' in response and response['items']:
                return response['items'][0]['id']
                
        except HttpError as e:
            self.logger.warning(f"API error resolving handle {handle}: {e}")
        except Exception as e:
            self.logger.warning(f"Error resolving handle {handle}: {e}")
        
        return None
    
    def _resolve_channel_id_from_username(self, username):
        """
        Resolve channel ID from legacy username using YouTube API.
        
        Args:
            username (str): YouTube username
            
        Returns:
            str or None: Channel ID if found
        """
        try:
            request = self.youtube.channels().list(
                part='id',
                forUsername=username
            )
            response = self._execute_with_retry(request)
            
            if 'items' in response and response['items']:
                return response['items'][0]['id']
                
        except HttpError as e:
            self.logger.warning(f"API error resolving username {username}: {e}")
        except Exception as e:
            self.logger.warning(f"Error resolving username {username}: {e}")
        
        return None
    
    def get_videos_from_playlist(self, playlist_id):
        """
        Retrieve all videos from a YouTube playlist.
        
        Args:
            playlist_id (str): YouTube playlist ID
            
        Returns:
            list: List of video dictionaries with metadata
        """
        videos = []
        next_page_token = None
        
        try:
            while True:
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = self._execute_with_retry(request)
                
                for item in response.get('items', []):
                    snippet = item.get('snippet', {})
                    resource_id = snippet.get('resourceId', {})
                    
                    video = {
                        'video_id': resource_id.get('videoId', ''),
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'published_at': snippet.get('publishedAt', ''),
                        'channel_title': snippet.get('channelTitle', ''),
                        'thumbnails': snippet.get('thumbnails', {})
                    }
                    videos.append(video)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
        except HttpError as e:
            self.logger.error(f"API error getting playlist {playlist_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error getting playlist {playlist_id}: {e}")
        
        return videos

    def _should_retry(self, exc):
        """Determine if the error warrants a retry."""
        status = getattr(exc.resp, 'status', 0)
        if status in [429, 500, 502, 503, 504]:
            return True
        try:
            content = exc.content.decode('utf-8')
            data = json.loads(content)
            error = data.get('error', {})
            errors = error.get('errors', [])
            for err in errors:
                reason = err.get('reason', '')
                if reason in ['tooManyRequests', 'internalError', 'serviceUnavailable']:
                    return True
                elif reason == 'quotaExceeded':
                    self.logger.warning('YouTube API quota exceeded. Please wait 24h or use a different API key.')
                    return False
        except Exception:
            pass
        return False

    def _log_api_error(self, exc, context):
        """Log detailed API error."""
        status_str = f"HTTP {getattr(exc.resp, 'status', 'unknown')}"
        self.logger.error(f'{context}: {status_str}')
        try:
            content = exc.content.decode('utf-8')
            data = json.loads(content)
            errors = data.get('error', {}).get('errors', [])
            for err in errors:
                reason = err.get('reason', '')
                message = err.get('message', '')
                self.logger.error(f'  Reason: {reason}, Message: {message}')
        except Exception as parse_err:
            self.logger.debug(f'Failed to parse error details: {parse_err}')

    def _execute_with_retry(self, request, max_retries=3):
        """Execute request with retry logic and backoff."""
        for attempt in range(max_retries):
            try:
                return request.execute()
            except HttpError as e:
                self._log_api_error(e, f'API request failed (attempt {attempt + 1}/{max_retries})')
                if attempt == max_retries - 1:
                    raise
                if self._should_retry(e):
                    sleep_time = min(2 ** attempt + attempt * 0.1, 60.0)
                    self.logger.info(f'Retrying in {sleep_time:.1f}s...')
                    time.sleep(sleep_time)
                else:
                    raise
            except Exception as e:
                self.logger.warning(f'Unexpected error on attempt {attempt + 1}: {e}')
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError('Max retries exceeded')

    def get_videos_from_channel(self, channel_id):
        """
        Retrieve all videos from a YouTube channel.
        
        Args:
            channel_id (str): YouTube channel ID
            
        Returns:
            list: List of video dictionaries with metadata
        """
        try:
            # Get channel's uploads playlist ID
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = self._execute_with_retry(request)
            
            if 'items' not in response or not response['items']:
                self.logger.warning(f"No channel found for ID {channel_id}")
                return []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            return self.get_videos_from_playlist(uploads_playlist_id)
            
        except HttpError as e:
            self.logger.error(f"API error getting channel {channel_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error getting channel {channel_id}: {e}")
        
        return []