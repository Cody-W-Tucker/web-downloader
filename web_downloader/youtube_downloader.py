#!/usr/bin/env python3
"""
YouTube Transcript Downloader: Main Controller

This module handles downloading transcripts from YouTube playlists, channels, or single videos.
It processes videos concurrently and saves transcripts as Markdown files.

Output is saved to a specified directory with filenames based on video titles.
"""

import argparse
import logging
import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv
import concurrent.futures

from .file_manager import FileManager
from .youtube_playlist_handler import YouTubePlaylistHandler
from .transcript_processor import TranscriptProcessor
from .utils.vpn_detector import VPNDetector


def setup_logging(log_level=logging.INFO):
    """
    Configure logging to console only.

    Args:
        log_level (int): Logging level

    Returns:
        logger: Configured logger object
    """
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console formatter
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


def parse_arguments():
    """
    Parse command line arguments for YouTube functionality.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Download transcripts from YouTube playlists, channels, or videos",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--youtube", help="YouTube playlist URL")
    parser.add_argument("--youtube-channel", help="YouTube channel URL or ID")
    parser.add_argument(
        "--youtube-api-key",
        help="YouTube Data API v3 key (or use YOUTUBE_API_KEY env var)",
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save extracted content",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (no flag: errors only, -v: info, -vv: debug)",
    )

    args = parser.parse_args()

    return args


def configure_log_level(verbosity):
    """
    Set log level based on verbosity.

    Args:
        verbosity (int): Verbosity level from command line

    Returns:
        int: Corresponding logging level
    """
    if verbosity == 0:
        return logging.ERROR  # Only show errors by default
    elif verbosity == 1:
        return logging.INFO
    else:
        return logging.DEBUG


def process_single_video(video, languages, translate_to, output_dir, logger):
    """Process a single YouTube video concurrently."""
    processor = TranscriptProcessor()
    file_manager = FileManager(output_dir=output_dir)
    video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
    try:
        docs = processor.load_transcript(
            video_url, language=languages, translation=translate_to
        )
        if not docs:
            logger.warning(f"No transcript available: {video['title']}")
            return False, video["title"]
        markdown = processor.format_transcript_as_markdown(docs, video_info=video)
        filepath = file_manager.save_youtube_transcript(video, markdown)
        if filepath:
            logger.info(f"Saved: {video['title']} -> {filepath}")
            return True, video["title"]
        else:
            logger.warning(f"Failed to save: {video['title']}")
            return False, video["title"]
    except Exception as e:
        logger.error(f"Error processing {video.get('title', 'unknown')}: {str(e)}")
        return False, video["title"]


def run_youtube(args):
    """Run YouTube transcript downloading with provided args."""
    # Parse command line arguments
    args = parse_arguments()

    # Configure logging based on verbosity
    log_level = configure_log_level(args.verbose)
    logger = setup_logging(log_level=log_level)
    load_dotenv()

    # Check VPN status before proceeding with YouTube downloads
    detector = VPNDetector()
    secured, status_msg = detector.check_mullvad_status()
    if not detector.prompt_user_if_needed(secured, status_msg):
        logger.info("User chose not to proceed without VPN")
        sys.exit(0)

    if args.verbose > 0:
        logger.info(f"Output directory: {args.output_dir}")

    youtube_url = args.youtube or args.youtube_channel
    api_key = args.youtube_api_key or os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error(
            "YouTube API key required (--youtube-api-key or YOUTUBE_API_KEY env var)"
        )
        sys.exit(1)

    languages = ["en"]
    translate_to = None

    logger.info(
        f"Processing YouTube {'playlist' if args.youtube else 'channel'}: {youtube_url}"
    )

    handler = YouTubePlaylistHandler(api_key)

    playlist_id = handler.extract_playlist_id(youtube_url)
    channel_id = handler.extract_channel_id(youtube_url)
    video_id = handler.extract_video_id(youtube_url)

    if playlist_id:
        videos = handler.get_videos_from_playlist(playlist_id)
    elif channel_id:
        videos = handler.get_videos_from_channel(channel_id)
    elif video_id:
        video = handler.get_video_metadata(video_id)
        if video:
            videos = [video]
        else:
            logger.error(f"Could not fetch metadata for video ID: {video_id}")
            sys.exit(1)
    else:
        logger.error(
            f"Could not extract playlist, channel, or video ID from: {youtube_url}"
        )
        sys.exit(1)

    if not videos:
        logger.info("No videos found.")
        sys.exit(0)

    logger.info(f"Found {len(videos)} videos.")

    successful = 0
    total = len(videos)
    max_workers = 10
    with tqdm(total=total, desc="Processing videos", unit="vid") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_title = {
                executor.submit(
                    process_single_video,
                    video,
                    languages,
                    translate_to,
                    args.output_dir,
                    logger,
                ): video["title"]
                for video in videos
            }
            for future in concurrent.futures.as_completed(future_to_title):
                try:
                    success, title = future.result()
                    if success:
                        successful += 1
                    pbar.update(1)
                except Exception as exc:
                    title = future_to_title[future]
                    logger.error(f"Thread generated exception for {title}: {exc}")
                    pbar.update(1)

    logger.info(f"YouTube processing complete: {successful}/{total} videos saved.")
    print(f"\nYouTube processing complete: {successful}/{total} videos")
    print(f"Output directory: {os.path.abspath(args.output_dir)}")


def main():
    """Main entry point for YouTube transcript downloading."""
    # Parse command line arguments
    args = parse_arguments()
    run_youtube(args)


if __name__ == "__main__":
    main()
