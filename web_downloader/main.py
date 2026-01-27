#!/usr/bin/env python3
"""
Website Text-to-Markdown Extractor: Main Controller

This module serves as the entry point and controller for the web-to-markdown conversion process.
It handles command line arguments, logging setup, and orchestrates the workflow.

By default, content is saved to a directory named after the website's domain,
with subdirectories reflecting the URL structure of the site.
"""

import argparse
import logging
import os
import sys
from tqdm import tqdm
from dotenv import load_dotenv

# Try relative imports first (when run as module)
try:
    from .crawler import RateLimitedSession, WebCrawler
    from .sitemap_parser import extract_sitemap_urls_recursive
    from .content_extractor import ContentExtractor
    from .markdown_converter import convert_html_to_markdown
    from .file_manager import FileManager
# Fall back to absolute imports (when run directly)
except ImportError:
    from crawler import RateLimitedSession, WebCrawler  # type: ignore[import-not-found,no-redef]
    from sitemap_parser import extract_sitemap_urls_recursive  # type: ignore[import-not-found,no-redef]
    from content_extractor import ContentExtractor  # type: ignore[import-not-found,no-redef]
    from markdown_converter import convert_html_to_markdown  # type: ignore[import-not-found,no-redef]
    from file_manager import FileManager  # type: ignore[import-not-found,no-redef]


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
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Extract content from websites and convert to Markdown",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "url",
        nargs="?",
        default=None,
        help="Root URL of the website to extract (required for web mode)",
    )

    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save extracted content (by default, uses the domain name)",
    )

    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum crawl depth for recursive crawling",
    )

    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between requests in seconds"
    )

    parser.add_argument(
        "--max-delay",
        type=float,
        default=3.0,
        help="Maximum delay for exponential backoff",
    )

    parser.add_argument(
        "--respect-robots",
        action="store_true",
        default=True,
        help="Whether to respect robots.txt directives",
    )

    parser.add_argument(
        "--ignore-robots",
        action="store_false",
        dest="respect_robots",
        help="Ignore robots.txt restrictions",
    )

    parser.add_argument(
        "--user-agent", default="WebToMarkdown/1.0", help="Custom user agent string"
    )

    parser.add_argument("--youtube", help="YouTube playlist URL")
    parser.add_argument("--youtube-channel", help="YouTube channel URL or ID")
    parser.add_argument(
        "--youtube-api-key",
        help="YouTube Data API v3 key (or use YOUTUBE_API_KEY env var)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (no flag: errors only, -v: info, -vv: debug)",
    )

    parser.add_argument(
        "--sitemap-only",
        action="store_true",
        help="Only use sitemap, don't crawl recursively if sitemap fails",
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


class ProcessingError(Exception):
    """Raised when URL processing fails."""

    pass


def process_url(url, session, content_extractor, file_manager):
    """
    Process a single URL: extract content, convert to Markdown, and save to file.

    Args:
        url (str): URL to process
        session (RateLimitedSession): Session for making requests
        content_extractor (ContentExtractor): Extractor for content
        file_manager (FileManager): Manager for saving files

    Returns:
        str: Path to saved file

    Raises:
        ProcessingError: If any step in processing fails
    """
    logger = logging.getLogger(__name__)

    try:
        # Fetch the page
        response = session.get(url)
        if not response.text:
            raise ProcessingError(f"No content from {url}")

        html_content = response.text

        # Extract content and metadata
        metadata, cleaned_content = content_extractor.extract_content(html_content, url)
        if not cleaned_content:
            raise ProcessingError(f"No content extracted from {url}")

        # Convert to Markdown
        markdown = convert_html_to_markdown(cleaned_content, metadata)
        if not markdown:
            raise ProcessingError(f"Failed to convert content from {url} to Markdown")

        # Save to file
        filepath = file_manager.save_markdown(markdown, url)
        if not filepath:
            raise ProcessingError(f"Failed to save Markdown for {url}")

        logger.info(f"Successfully processed {url} -> {filepath}")
        return filepath

    except Exception as e:
        if isinstance(e, ProcessingError):
            logger.info(str(e))
        else:
            logger.error(f"Error processing {url}: {str(e)}")
        raise


def main():
    """Main entry point of the application."""
    # Parse command line arguments
    args = parse_arguments()

    # Dispatch to YouTube if YouTube args are provided
    if args.youtube or args.youtube_channel:
        try:
            import youtube_downloader

            youtube_downloader.run_youtube(args)
        except ImportError:
            from youtube_downloader import run_youtube  # type: ignore[import-not-found]

            run_youtube(args)
        return

    # Configure logging based on verbosity
    log_level = configure_log_level(args.verbose)
    logger = setup_logging(log_level=log_level)
    load_dotenv()

    if args.verbose > 0:
        logger.info(f"Starting extraction from URL: {args.url}")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"Crawl depth: {args.depth}")
        logger.info(f"Request delay: {args.delay}s")
        logger.info(f"Maximum delay: {args.max_delay}s")
        logger.info(f"Respect robots.txt: {args.respect_robots}")
        logger.info(f"User agent: {args.user_agent}")

        if args.url is None:
            logger.error("URL required for web crawling mode.")
            sys.exit(1)

        # Initialize the session
        session = RateLimitedSession(
            delay=args.delay,
            max_delay=args.max_delay,
            respect_robots=args.respect_robots,
            user_agent=args.user_agent,
        )

        # Initialize other components
        content_extractor = ContentExtractor()
        file_manager = FileManager(output_dir=args.output_dir)

        # Try to extract URLs from sitemap first
        logger.info("Attempting to extract URLs from sitemap...")
        urls = extract_sitemap_urls_recursive(session, args.url)

        if not urls and not args.sitemap_only:
            logger.info(
                "No sitemap found or no URLs in sitemap. Falling back to recursive crawling..."
            )
            crawler = WebCrawler(args.url, session, max_depth=args.depth)
            url_content_map = crawler.crawl()
            urls = list(url_content_map.keys())

        if not urls:
            logger.error(
                "No URLs found to process. Check if the site has a sitemap or try changing parameters."
            )
            print("Error: No URLs found to process.")
            sys.exit(1)

        # Process each URL
        successful = 0
        failed = 0
        logger.info(f"Processing {len(urls)} URLs...")

        try:
            with tqdm(
                total=len(urls), desc="Processing URLs", unit="URL"
            ) as progress_bar:
                for url in urls:
                    try:
                        process_url(url, session, content_extractor, file_manager)
                        successful += 1
                    except ProcessingError:
                        failed += 1
                    progress_bar.update(1)
        except KeyboardInterrupt:
            logger.warning("Process interrupted by user")
            print("\nProcess interrupted by user")

        # Report statistics
        logger.info(f"Extraction complete. Successfully processed {successful} URLs.")
        if failed > 0:
            logger.warning(f"Failed to process {failed} URLs.")

        print("\nExtraction complete.")
        print(f"Successfully processed: {successful} URLs")
        print(f"Failed to process: {failed} URLs")
        print(f"Output directory: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
