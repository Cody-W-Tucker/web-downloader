"""
YouTube Transcript Processor using youtube-transcript-api

This module provides functionality to load, format, and convert YouTube transcripts to Markdown.
Supports language preferences and available translations.
"""

import logging
from datetime import datetime

try:
    from youtube_transcript_api._api import YouTubeTranscriptApi
    from langchain_core.documents import Document
except ImportError as e:
    raise ImportError(
        f"Required packages not installed: {e}. Run 'pip install youtube-transcript-api langchain-core'"
    )


class TranscriptProcessor:
    """
    Processor for loading and formatting YouTube transcripts using youtube-transcript-api.

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
        Load transcript using YouTube Transcript API with fallback to any available language.

        Args:
            youtube_url (str): Full YouTube video URL
            language (list): Preferred languages (e.g. ["en", "es"])
            translation (str or None): Translation language if available
            add_video_info (bool): Add video metadata

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
            # Get list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = list(transcript_list)

            if not available_transcripts:
                self.logger.warning(f"No transcripts available for {youtube_url}")
                return []

            # Try to find transcript in preferred languages
            transcript = None

            # First try preferred languages
            for lang in language:
                try:
                    transcript = transcript_list.find_transcript([lang]).fetch()
                    break
                except Exception:
                    continue

            # If no preferred language worked, try any available transcript
            if transcript is None:
                for t in available_transcripts:
                    try:
                        transcript = t.fetch()
                        break
                    except Exception:
                        continue

            if transcript is None:
                self.logger.warning(f"Could not fetch any transcript for {youtube_url}")
                return []

            # Format as text with timestamps
            content = "\n".join(
                [f"[{int(entry['start'])}s] {entry['text']}" for entry in transcript]
            )
            doc = Document(page_content=content, metadata={"source": youtube_url})
            self.logger.info(f"Successfully loaded transcript for {youtube_url}")
            return [doc]
        except Exception as e:
            self.logger.warning(
                f"Error processing transcript for {youtube_url}: {str(e)}"
            )
            return []

    def _format_transcript(self, docs):
        """
        Format transcript documents with timestamps and content.

        Args:
            docs (list): List of Document objects from YouTube Transcript API

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
        md += "source: YouTube Transcript (via youtube-transcript-api)\n"
        md += f"date_extracted: {datetime.now().isoformat()}\n"
        md += "---\n\n"
        md += formatted

        return md
