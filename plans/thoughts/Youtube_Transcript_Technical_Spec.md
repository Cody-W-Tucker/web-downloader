---
title: "YouTube Transcript Tool Technical Specification"
dateCreated: 2023-06-10
dateModified: 2023-06-10
---

# YouTube Transcript Tool Technical Specification

This document provides detailed technical specifications for implementing the YouTube transcript extraction functionality as outlined in the implementation plan.

## 1. Dependencies

Add the following dependencies to `requirements.txt`:

```
langchain>=0.0.312
langchain-community>=0.0.9
youtube-transcript-api>=0.6.1
pytube>=15.0.0
google-api-python-client>=2.100.0
python-dotenv>=1.0.0
```

## 2. Environment Configuration

Create a `.env.example` file with the following structure:

```
# YouTube API key for accessing YouTube Data API
YOUTUBE_API_KEY=your_api_key_here

# Default language for transcripts
DEFAULT_LANGUAGE=en

# Default output directory
DEFAULT_OUTPUT_DIR=transcripts
```

Instruct users to copy this to `.env` and fill in their own API key.

## 3. Component Implementation

### 3.1 YouTube Playlist Handler (`youtube_playlist_handler.py`)

This module will handle fetching video IDs from playlists and channels.

```python
#!/usr/bin/env python3
"""
YouTube Playlist Handler Module

This module provides functionality to extract video IDs from YouTube playlists and channels.
"""

import logging
import os
from typing import List, Optional
from urllib.parse import parse_qs, urlparse

import googleapiclient.discovery
import googleapiclient.errors
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class YouTubePlaylistHandler:
    """A class that handles extracting video IDs from YouTube playlists and channels."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the YouTube API client.
        
        Args:
            api_key: YouTube Data API key. If None, tries to load from environment.
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key not provided and not found in environment")
        
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=self.api_key
        )
    
    def extract_playlist_id(self, playlist_url: str) -> str:
        """
        Extract playlist ID from a YouTube playlist URL.
        
        Args:
            playlist_url: YouTube playlist URL
            
        Returns:
            Playlist ID
        """
        parsed_url = urlparse(playlist_url)
        
        if parsed_url.netloc not in ('www.youtube.com', 'youtube.com'):
            raise ValueError(f"Not a YouTube URL: {playlist_url}")
        
        query_params = parse_qs(parsed_url.query)
        
        playlist_id = query_params.get('list', [None])[0]
        if not playlist_id:
            raise ValueError(f"Could not extract playlist ID from URL: {playlist_url}")
        
        return playlist_id
    
    def extract_channel_id(self, channel_url: str) -> str:
        """
        Extract channel ID from a YouTube channel URL.
        
        Args:
            channel_url: YouTube channel URL
            
        Returns:
            Channel ID
        """
        parsed_url = urlparse(channel_url)
        
        if parsed_url.netloc not in ('www.youtube.com', 'youtube.com'):
            raise ValueError(f"Not a YouTube URL: {channel_url}")
        
        path_parts = parsed_url.path.strip('/').split('/')
        
        # Handle different channel URL formats
        if len(path_parts) < 2:
            raise ValueError(f"Invalid channel URL format: {channel_url}")
        
        if path_parts[0] == 'channel':
            # Direct channel ID: youtube.com/channel/CHANNEL_ID
            return path_parts[1]
        elif path_parts[0] in ('c', 'user', '@'):
            # Custom URL: youtube.com/c/NAME, youtube.com/user/NAME, or youtube.com/@NAME
            # Need to look up the channel ID
            channel_name = path_parts[1]
            request = self.youtube.search().list(
                part="snippet",
                q=channel_name,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            
            if response.get("items"):
                return response["items"][0]["id"]["channelId"]
            else:
                raise ValueError(f"Could not find channel ID for: {channel_url}")
        else:
            raise ValueError(f"Unsupported channel URL format: {channel_url}")
    
    def get_channel_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Get the uploads playlist ID for a channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Uploads playlist ID
        """
        request = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        
        if not response.get("items"):
            raise ValueError(f"Could not find channel with ID: {channel_id}")
        
        # The uploads playlist ID is in the contentDetails.relatedPlaylists.uploads field
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return uploads_playlist_id
    
    def get_videos_from_playlist(self, playlist_id: str) -> List[dict]:
        """
        Get all videos from a playlist.
        
        Args:
            playlist_id: YouTube playlist ID
            
        Returns:
            List of video dictionaries with id and metadata
        """
        videos = []
        next_page_token = None
        
        while True:
            request = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            
            try:
                response = request.execute()
            except googleapiclient.errors.HttpError as e:
                logger.error(f"YouTube API error: {str(e)}")
                break
            
            # Extract video information
            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                title = item["snippet"]["title"]
                
                # Skip deleted or private videos
                if title == "Deleted video" or title == "Private video":
                    logger.warning(f"Skipping unavailable video: {video_id}")
                    continue
                
                # Get additional video metadata
                video_info = self.get_video_metadata(video_id)
                if video_info:
                    videos.append(video_info)
            
            # Check if there are more pages
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        return videos
    
    def get_videos_from_channel(self, channel_url: str) -> List[dict]:
        """
        Get all videos from a channel.
        
        Args:
            channel_url: YouTube channel URL
            
        Returns:
            List of video dictionaries with id and metadata
        """
        # Get channel ID
        channel_id = self.extract_channel_id(channel_url)
        
        # Get uploads playlist ID
        uploads_playlist_id = self.get_channel_uploads_playlist_id(channel_id)
        
        # Get videos from uploads playlist
        return self.get_videos_from_playlist(uploads_playlist_id)
    
    def get_video_metadata(self, video_id: str) -> Optional[dict]:
        """
        Get metadata for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary with video metadata, or None if video not found
        """
        request = self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        
        try:
            response = request.execute()
        except googleapiclient.errors.HttpError as e:
            logger.error(f"YouTube API error fetching metadata for video {video_id}: {str(e)}")
            return None
        
        if not response.get("items"):
            logger.warning(f"Video not found: {video_id}")
            return None
        
        video_data = response["items"][0]
        
        # Extract relevant metadata
        snippet = video_data["snippet"]
        
        return {
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "duration": video_data["contentDetails"].get("duration", ""),
            "view_count": video_data["statistics"].get("viewCount", "0"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }
```

### 3.2 Transcript Processor (`transcript_processor.py`)

This module will handle processing transcripts from LangChain documents.

```python
#!/usr/bin/env python3
"""
Transcript Processor Module

This module provides functionality to process YouTube transcripts from LangChain document loaders.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from langchain_community.document_loaders import YoutubeLoader

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """A class that processes YouTube transcripts from LangChain documents."""
    
    def __init__(self, languages: Optional[List[str]] = None, translation: Optional[str] = None):
        """
        Initialize the transcript processor.
        
        Args:
            languages: List of languages to try in order of preference (e.g., ["en", "es"])
            translation: Language code to translate transcript to, if available
        """
        self.languages = languages or ["en"]
        self.translation = translation
    
    def load_transcript(self, video_url: str, add_video_info: bool = True) -> Optional[dict]:
        """
        Load transcript for a YouTube video using LangChain.
        
        Args:
            video_url: YouTube video URL
            add_video_info: Whether to add video metadata
            
        Returns:
            Dictionary with transcript content and metadata, or None if transcript not available
        """
        try:
            # Create YoutubeLoader with specified languages and translation
            loader = YoutubeLoader.from_youtube_url(
                video_url,
                add_video_info=add_video_info,
                language=self.languages,
                translation=self.translation
            )
            
            # Load documents
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No transcript found for: {video_url}")
                return None
            
            # Extract content and metadata from the first document
            doc = documents[0]
            transcript_text = doc.page_content
            metadata = doc.metadata
            
            # Process the transcript text to format it nicely
            formatted_transcript = self._format_transcript(transcript_text)
            
            return {
                "content": formatted_transcript,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error loading transcript for {video_url}: {str(e)}")
            return None
    
    def _format_transcript(self, transcript_text: str) -> str:
        """
        Format the transcript text to be more readable.
        
        Args:
            transcript_text: Raw transcript text from LangChain
            
        Returns:
            Formatted transcript text
        """
        # First, check if there are timestamps in the transcript
        # LangChain's YoutubeLoader usually includes timestamps
        has_timestamps = bool(re.search(r'\[\d+:\d+:\d+\]|\[\d+:\d+\]', transcript_text))
        
        if has_timestamps:
            # Format existing timestamps consistently
            # Replace all timestamp formats with a standard format [HH:MM:SS]
            formatted_text = re.sub(
                r'\[(\d+):(\d+):(\d+)\]|\[(\d+):(\d+)\]',
                lambda m: self._format_timestamp(m),
                transcript_text
            )
            
            # Ensure timestamps start on a new line
            formatted_text = re.sub(
                r'([^\n])\[(\d+):(\d+):(\d+)\]',
                r'\1\n[\2:\3:\4]',
                formatted_text
            )
            
            # Clean up any extra newlines
            formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
            
            return formatted_text
        else:
            # If no timestamps, try to split into reasonable paragraphs
            # Split the text if there are more than 150 characters without a newline
            paragraphs = []
            current_paragraph = []
            
            for line in transcript_text.split('\n'):
                current_paragraph.append(line)
                paragraph_text = ' '.join(current_paragraph)
                
                if len(paragraph_text) > 150 and not line.endswith(('?', '!', '.')):
                    paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = []
            
            # Add the last paragraph
            if current_paragraph:
                paragraphs.append(' '.join(current_paragraph))
            
            # Join paragraphs with double newlines
            return '\n\n'.join(paragraphs)
    
    def _format_timestamp(self, match) -> str:
        """
        Format a timestamp match to the standard format [HH:MM:SS].
        
        Args:
            match: A regex match object with timestamp groups
            
        Returns:
            Formatted timestamp string
        """
        # Check which format matched
        if match.group(1) is not None:
            # Format: [HH:MM:SS]
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = int(match.group(3))
        else:
            # Format: [MM:SS]
            hours = 0
            minutes = int(match.group(4))
            seconds = int(match.group(5))
        
        # Return the standardized format
        return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
    
    def format_transcript_as_markdown(self, transcript_data: dict, video_info: dict) -> str:
        """
        Format the transcript data as a Markdown document.
        
        Args:
            transcript_data: Transcript data from load_transcript
            video_info: Video metadata from YouTube API
            
        Returns:
            Markdown content
        """
        if not transcript_data or not transcript_data.get("content"):
            return ""
        
        # Build the front matter
        front_matter = [
            "---",
            f"title: \"{video_info['title']}\"",
            f"source_url: \"{video_info['url']}\"",
            f"channel: \"{video_info['channel_title']}\"",
            f"channel_url: \"https://www.youtube.com/channel/{video_info['channel_id']}\"",
            f"published_at: \"{video_info['published_at']}\"",
            f"date_extracted: \"{datetime.now().isoformat()}\"",
            "type: \"youtube_transcript\"",
            "---"
        ]
        
        # Add a blockquote with the description if available
        if video_info.get("description"):
            # Limit description length for front matter
            description = video_info["description"]
            if len(description) > 300:
                description = description[:297] + "..."
            
            # Replace all newlines with spaces for the blockquote
            description = description.replace("\n", " ").strip()
            front_matter.append("")
            front_matter.append(f"> {description}")
        
        # Build the document content
        content_parts = [
            "",
            f"# {video_info['title']}",
            "",
            f"- **Video URL**: {video_info['url']}",
            f"- **Channel**: {video_info['channel_title']}",
            f"- **Published**: {video_info['published_at'].split('T')[0]}",
            f"- **Views**: {video_info['view_count']}",
            "",
            "## Transcript",
            "",
            transcript_data["content"]
        ]
        
        # Combine all parts
        return "\n".join(front_matter + content_parts)
```

### 3.3 Main Module Extensions (`main.py`)

Add YouTube-specific command line arguments and workflow to the main module:

```python
# Add these imports to the top of main.py
from .youtube_playlist_handler import YouTubePlaylistHandler
from .transcript_processor import TranscriptProcessor

# Add these to the parse_arguments function
parser.add_argument(
    "--youtube-playlist",
    help="YouTube playlist URL to extract transcripts from"
)

parser.add_argument(
    "--youtube-channel",
    help="YouTube channel URL to extract transcripts from"
)

parser.add_argument(
    "--language",
    default="en",
    help="Comma-separated list of language codes for transcripts in order of preference"
)

parser.add_argument(
    "--translate-to",
    help="Language code to translate transcripts to, if available"
)

parser.add_argument(
    "--youtube-api-key",
    help="YouTube Data API key (can also be set as YOUTUBE_API_KEY environment variable)"
)

# Add this function to main.py
def process_youtube_url(
    url_type, url, languages, translation, api_key, file_manager, output_dir
):
    """
    Process YouTube URLs (playlist or channel) and extract transcripts.
    
    Args:
        url_type (str): Type of URL ('playlist' or 'channel')
        url (str): YouTube URL
        languages (list): List of language codes in order of preference
        translation (str): Language code to translate to, or None
        api_key (str): YouTube API key
        file_manager (FileManager): File manager instance
        output_dir (str): Output directory
        
    Returns:
        tuple: (successful_count, failed_count)
    """
    logger = logging.getLogger(__name__)
    
    # Initialize handlers
    youtube_handler = YouTubePlaylistHandler(api_key)
    transcript_processor = TranscriptProcessor(languages=languages, translation=translation)
    
    # Get video list based on URL type
    if url_type == 'playlist':
        try:
            logger.info(f"Extracting videos from playlist: {url}")
            playlist_id = youtube_handler.extract_playlist_id(url)
            videos = youtube_handler.get_videos_from_playlist(playlist_id)
            
            if not videos:
                logger.error("No videos found in playlist")
                return 0, 0
                
            logger.info(f"Found {len(videos)} videos in playlist")
        except Exception as e:
            logger.error(f"Error extracting playlist videos: {str(e)}")
            return 0, 0
    else:  # channel
        try:
            logger.info(f"Extracting videos from channel: {url}")
            videos = youtube_handler.get_videos_from_channel(url)
            
            if not videos:
                logger.error("No videos found in channel")
                return 0, 0
                
            logger.info(f"Found {len(videos)} videos in channel")
        except Exception as e:
            logger.error(f"Error extracting channel videos: {str(e)}")
            return 0, 0
    
    # Process each video
    successful = 0
    failed = 0
    
    try:
        with tqdm(total=len(videos), desc="Processing videos", unit="video") as progress_bar:
            for video in videos:
                video_url = video['url']
                try:
                    # Load transcript
                    transcript_data = transcript_processor.load_transcript(video_url)
                    
                    if not transcript_data:
                        logger.warning(f"No transcript available for: {video_url}")
                        failed += 1
                        progress_bar.update(1)
                        continue
                    
                    # Format as Markdown
                    markdown_content = transcript_processor.format_transcript_as_markdown(
                        transcript_data, video
                    )
                    
                    # Save to file
                    filepath = file_manager.save_youtube_transcript(
                        markdown_content, video, output_dir
                    )
                    
                    if filepath:
                        logger.info(f"Saved transcript for {video['title']} to {filepath}")
                        successful += 1
                    else:
                        logger.error(f"Failed to save transcript for {video['title']}")
                        failed += 1
                
                except Exception as e:
                    logger.error(f"Error processing video {video_url}: {str(e)}")
                    failed += 1
                
                progress_bar.update(1)
    
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print("\nProcess interrupted by user")
    
    return successful, failed

# Modify the main function to add a YouTube processing branch
def main():
    # Existing code...
    
    # Check if we're using YouTube functionality
    if args.youtube_playlist or args.youtube_channel:
        # Parse languages
        languages = args.language.split(',') if args.language else ['en']
        
        # Set up file manager
        output_dir = args.output_dir
        file_manager = FileManager(output_dir=output_dir)
        
        # Get API key
        api_key = args.youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            logger.error("YouTube API key not provided. Use --youtube-api-key or set YOUTUBE_API_KEY environment variable.")
            sys.exit(1)
        
        # Process based on URL type
        if args.youtube_playlist:
            successful, failed = process_youtube_url(
                'playlist', args.youtube_playlist, languages, args.translate_to,
                api_key, file_manager, output_dir
            )
        else:
            successful, failed = process_youtube_url(
                'channel', args.youtube_channel, languages, args.translate_to,
                api_key, file_manager, output_dir
            )
        
        # Report statistics
        print(f"\nTranscript extraction complete.")
        print(f"Successfully processed: {successful} videos")
        print(f"Failed to process: {failed} videos")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        
        return
    
    # Existing web crawling code...
```

### 3.4 File Manager Extensions (`file_manager.py`)

Add YouTube-specific file handling to the `FileManager` class:

```python
# Add this method to the FileManager class in file_manager.py

def save_youtube_transcript(self, markdown_content, video_info, base_dir=None):
    """
    Save a YouTube transcript to a file in an appropriate directory structure.
    
    Args:
        markdown_content (str): Markdown content to save
        video_info (dict): Video metadata
        base_dir (str, optional): Base directory to save to. If None, uses self.output_dir
        
    Returns:
        str: Path to the saved file, or None if failed
    """
    try:
        # Determine the output directory
        if base_dir:
            output_dir = base_dir
        else:
            output_dir = self.output_dir
            
        # Create a directory structure based on the channel
        channel_name = self._sanitize_filename(video_info.get('channel_title', 'Unknown Channel'))
        channel_dir = os.path.join(output_dir, channel_name)
        
        # Create the directory
        if not self._create_directory(channel_dir):
            return None
            
        # Create a filename based on the video title and ID
        video_title = video_info.get('title', 'Untitled Video')
        video_id = video_info.get('id', '')
        
        filename = f"{self._sanitize_filename(video_title)}-{video_id}.md"
        filepath = os.path.join(channel_dir, filename)
        
        # Write the content to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        return filepath
    
    except Exception as e:
        logger.error(f"Error saving YouTube transcript: {str(e)}")
        return None
```

## 4. Integration Testing

Here's a sample integration test script to verify the complete pipeline:

```python
#!/usr/bin/env python3
"""
Integration test for the YouTube transcript extraction functionality.
"""

import logging
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.file_manager import FileManager
from src.youtube_playlist_handler import YouTubePlaylistHandler
from src.transcript_processor import TranscriptProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test constants
TEST_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLkDaE6sCZn6Ec-XTbcX1uRg2_u4xOEky0"  # Andrew Ng's Deep Learning course
TEST_OUTPUT_DIR = "test_output"
TEST_API_KEY = os.getenv("YOUTUBE_API_KEY")

def test_playlist_extraction():
    """Test extracting transcripts from a playlist."""
    if not TEST_API_KEY:
        logger.error("YOUTUBE_API_KEY environment variable not set")
        return False
        
    # Initialize components
    handler = YouTubePlaylistHandler(TEST_API_KEY)
    processor = TranscriptProcessor(languages=["en"])
    file_manager = FileManager(output_dir=TEST_OUTPUT_DIR)
    
    # Create output directory
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    # Get videos from playlist
    try:
        playlist_id = handler.extract_playlist_id(TEST_PLAYLIST_URL)
        videos = handler.get_videos_from_playlist(playlist_id)
        
        if not videos:
            logger.error("No videos found in test playlist")
            return False
            
        logger.info(f"Found {len(videos)} videos in test playlist")
        
        # Process first 3 videos only for testing
        for i, video in enumerate(videos[:3]):
            video_url = video['url']
            
            # Load transcript
            transcript_data = processor.load_transcript(video_url)
            
            if not transcript_data:
                logger.warning(f"No transcript available for: {video_url}")
                continue
                
            # Format as Markdown
            markdown_content = processor.format_transcript_as_markdown(
                transcript_data, video
            )
            
            # Save to file
            filepath = file_manager.save_youtube_transcript(
                markdown_content, video, TEST_OUTPUT_DIR
            )
            
            if filepath:
                logger.info(f"Saved transcript for {video['title']} to {filepath}")
            else:
                logger.error(f"Failed to save transcript for {video['title']}")
                
        return True
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_playlist_extraction()
    if success:
        logger.info("Integration test passed")
    else:
        logger.error("Integration test failed")
```

## 5. Usage Examples

### Command Line Usage

```bash
# Extract transcripts from a YouTube playlist
python -m src --youtube-playlist "https://www.youtube.com/playlist?list=PLkDaE6sCZn6Ec-XTbcX1uRg2_u4xOEky0" --output-dir "transcripts"

# Extract transcripts from a YouTube channel
python -m src --youtube-channel "https://www.youtube.com/c/AndrewNgAI" --output-dir "transcripts"

# Extract with language preferences and translation
python -m src --youtube-playlist "https://www.youtube.com/playlist?list=PLkDaE6sCZn6Ec-XTbcX1uRg2_u4xOEky0" --language "en,fr,es" --translate-to "en"
```

### API Usage

The components can also be used programmatically:

```python
from src.youtube_playlist_handler import YouTubePlaylistHandler
from src.transcript_processor import TranscriptProcessor
from src.file_manager import FileManager

# Initialize components
handler = YouTubePlaylistHandler(api_key="your_api_key")
processor = TranscriptProcessor(languages=["en"])
file_manager = FileManager(output_dir="transcripts")

# Get videos from a playlist
playlist_url = "https://www.youtube.com/playlist?list=PLkDaE6sCZn6Ec-XTbcX1uRg2_u4xOEky0"
videos = handler.get_videos_from_playlist(
    handler.extract_playlist_id(playlist_url)
)

# Process each video
for video in videos:
    # Get transcript
    transcript_data = processor.load_transcript(video['url'])
    
    if transcript_data:
        # Format as Markdown
        markdown = processor.format_transcript_as_markdown(transcript_data, video)
        
        # Save to file
        file_manager.save_youtube_transcript(markdown, video)
```

## 6. Error Handling

The implementation should handle these common error cases:

1. **Missing API Key**: Check for API key in both command line args and environment variables
2. **Invalid URL**: Validate YouTube URLs before processing
3. **API Quotas**: Implement backoff strategies for API request limits
4. **Missing Transcripts**: Skip videos without available transcripts
5. **Language Preferences**: Try multiple languages in order of preference
6. **File System Errors**: Handle file writing exceptions gracefully

## 7. Performance Considerations

1. **Pagination**: Process large playlists/channels in batches
2. **Parallel Processing**: Consider implementing concurrent transcript fetching for large playlists
3. **Caching**: Cache API responses to reduce API calls
4. **Progress Reporting**: Use tqdm for progress bars to keep users informed

## 8. Future Enhancements

1. **Audio Transcription**: Add support for generating transcripts using Whisper API for videos without captions
2. **Intelligent Chunking**: Improve paragraph detection and timestamp processing
3. **Video Metadata Enrichment**: Add more metadata like topics, tags, etc.
4. **Custom Formatting**: Allow users to specify custom Markdown templates 