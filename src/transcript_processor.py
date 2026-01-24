"""
YouTube Transcript Processor using LangChain YoutubeLoader

This module provides functionality to load, format, and convert YouTube transcripts to Markdown.
Supports language preferences and available translations.
"""

import logging
from datetime import datetime

try:
    from langchain_community.document_loaders import YoutubeLoader
except ImportError as e:
    raise ImportError(
        "langchain-community not installed. Run 'pip install langchain-community'"
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
        Load transcript using YoutubeLoader.

        Args:
            youtube_url (str): Full YouTube video URL
            language (list): Preferred languages (e.g. ["en", "es"])
            translation (str or None): Translation language if available
            add_video_info (bool): Add video metadata from yt-dlp/pytube

        Returns:
            list: List of LangChain Document objects with transcripts
        """
        try:
            loader = YoutubeLoader.from_youtube_url(
                youtube_url,
                language=language,
                translation=translation,
                add_video_info=add_video_info,
            )
            docs = loader.load()
            self.logger.info(f"Successfully loaded transcript for {youtube_url}")
            return docs
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
