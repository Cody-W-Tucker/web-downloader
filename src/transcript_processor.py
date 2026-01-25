"""
YouTube Transcript Processor using LangChain YoutubeLoader

This module provides functionality to load, format, and convert YouTube transcripts to Markdown.
Supports language preferences and available translations.
"""

import logging
from datetime import datetime

try:
    from langchain_core.documents import Document
    from youtube_transcript_api._api import YouTubeTranscriptApi
except ImportError as e:
    raise ImportError(
        f"Required packages not installed: {e}. Run 'pip install langchain-core youtube-transcript-api'"
    )


class TranscriptProcessor:
    """
    Processor for loading and formatting YouTube transcripts using LangChain YoutubeLoader.

    Handles multiple language preferences, translations, video info, and error cases.
    """

    def __init__(self):
        """
        Initialize the transcript processor.
        """
        self.logger = logging.getLogger(__name__)

    def load_transcript(
        self, youtube_url: str, language=["en"], translation=None, add_video_info=True
    ):
        """
        Load transcript using YouTubeTranscriptApi.

        Args:
            youtube_url (str): Full YouTube video URL
            language (list): Preferred languages (e.g. ["en", "es"])
            translation (str or None): Translation language if available (not used)
            add_video_info (bool): Add video metadata (not used)

        Returns:
            list: List of LangChain Document objects with transcripts
        """
        # Extract video ID from URL
        import re

        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", youtube_url)
        if not match:
            self.logger.error(f"Could not extract video ID from {youtube_url}")
            return []
        video_id = match.group(1)

        try:
            # Get transcript using direct API, try preferred languages first
            transcript = None
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=language
                )
            except Exception:
                # Try without language restriction
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
            # Format as text with timestamps
            content = "\n".join(
                [f"[{int(entry['start'])}s] {entry['text']}" for entry in transcript]
            )
            doc = Document(page_content=content)
            self.logger.info(f"Successfully loaded transcript for {youtube_url}")
            return [doc]
        except Exception as e:
            self.logger.warning(f"No transcript available for {youtube_url}: {str(e)}")
            return []

    def _format_transcript(self, docs):
        """
        Format transcript documents with timestamps and content.

        Args:
            docs (list): List of Document objects from YoutubeLoader

        Returns:
            str: Formatted transcript text
        """
        if not docs:
            return ""

        transcript_lines = []
        for doc in docs:
            lines = doc.page_content.strip().split("\n")
            transcript_lines.extend(line.strip() for line in lines if line.strip())

        return "\n".join(transcript_lines)

    def format_transcript_as_markdown(self, docs, video_info=None):
        """
        Format transcript as Markdown with frontmatter.

        Args:
            docs (list): List of Document objects
            video_info (dict): Video metadata from YouTubePlaylistHandler

        Returns:
            str: Complete Markdown content ready for FileManager.save_markdown()

        Raises:
            ValueError: If no transcript content available
        """
        formatted = self._format_transcript(docs)
        if not formatted:
            raise ValueError("No transcript content to format")

        md = "---\n"
        if video_info:
            md += f"title: {video_info.get('title', 'Unknown Video')}\n"
            md += f"video_id: {video_info.get('video_id', '')}\n"
            md += f"channel_title: {video_info.get('channel_title', '')}\n"
            md += f"published_at: {video_info.get('published_at', '')}\n"
            md += f"youtube_url: https://www.youtube.com/watch?v={video_info.get('video_id', '')}\n"
        md += "source: YouTube Transcript (via LangChain YoutubeLoader)\n"
        md += f"date_extracted: {datetime.now().isoformat()}\n"
        md += "---\n\n"
        md += formatted

        return md
