#!/usr/bin/env python3
"""
Website Text-to-Markdown Extractor: Main Controller

This module serves as the entry point and controller for the web-to-markdown conversion process.
It handles command line arguments, logging setup, and orchestrates the workflow.

By default, content is saved to a directory named after the website's domain,
with subdirectories reflecting the URL structure of the site.

Uses defuddle for content extraction (Node.js required).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from tqdm import tqdm

# Try relative imports (when used as a module)
try:
    from .robots_parser import RobotsHandler
    from .crawler import RateLimitedSession, WebCrawler
    from .sitemap_parser import extract_sitemap_urls_recursive
    from .defuddle_extractor import DefuddleExtractor
    from .file_manager import FileManager
# Fall back to absolute imports (when run directly)
except ImportError:
    from robots_parser import RobotsHandler
    from crawler import RateLimitedSession, WebCrawler
    from sitemap_parser import extract_sitemap_urls_recursive
    from defuddle_extractor import DefuddleExtractor
    from file_manager import FileManager


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
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
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
        description="Extract content from websites and convert to Markdown (using defuddle)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "url",
        help="Root URL of the website to extract"
    )
    
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save extracted content (by default, uses the domain name)"
    )
    
    parser.add_argument(
        "--depth",
        type=int,
        default=5,
        help="Maximum crawl depth for recursive crawling"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds"
    )
    
    parser.add_argument(
        "--max-delay",
        type=float,
        default=3.0,
        help="Maximum delay for exponential backoff"
    )
    
    parser.add_argument(
        "--respect-robots",
        action="store_true",
        default=True,
        help="Whether to respect robots.txt directives"
    )
    
    parser.add_argument(
        "--ignore-robots",
        action="store_false",
        dest="respect_robots",
        help="Ignore robots.txt restrictions"
    )
    
    parser.add_argument(
        "--user-agent",
        default="WebToMarkdown/1.0",
        help="Custom user agent string"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (no flag: errors only, -v: info, -vv: debug)"
    )
    
    parser.add_argument(
        "--sitemap-only",
        action="store_true",
        help="Only use sitemap, don't crawl recursively if sitemap fails"
    )
    
    parser.add_argument(
        "--node-path",
        default=None,
        help="Path to Node.js executable (optional, will auto-detect)"
    )
    
    parser.add_argument(
        "--format",
        default="markdown",
        choices=["html", "markdown", "json"],
        help="Output format for extracted content (default: markdown)"
    )
    
    parser.add_argument(
        "--content-selector",
        default=None,
        help="CSS selector to use as main content element (bypasses auto-detection)"
    )
    
    # Pipeline toggle options
    parser.add_argument(
        "--no-remove-hidden",
        action="store_true",
        help="Don't remove elements hidden via CSS"
    )
    
    parser.add_argument(
        "--no-remove-low-scoring",
        action="store_true",
        help="Don't remove low-scoring content blocks"
    )
    
    parser.add_argument(
        "--no-standardize",
        action="store_true",
        help="Don't standardize HTML elements (headings, code blocks, footnotes)"
    )
    
    parser.add_argument(
        "--keep-images",
        action="store_false",
        dest="remove_images",
        default=True,
        help="Keep images in the output (default: removed)"
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


def process_url(url, session, content_extractor, file_manager, output_format='markdown', pipeline_options=None):
    """
    Process a single URL: extract content using defuddle, and save to file.
    
    Args:
        url (str): URL to process
        session (RateLimitedSession): Session for making requests
        content_extractor (DefuddleExtractor): Defuddle extractor for content
        file_manager (FileManager): Manager for saving files
        output_format (str): Output format - 'html', 'markdown', or 'json'
        pipeline_options (dict): Pipeline toggle options for defuddle
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Fetch the page
        response = session.get(url)
        if not response or not hasattr(response, 'text') or not response.text:
            logger.info(f"No response or empty content from {url}")
            return False
            
        html_content = response.text
        
        # Extract content and metadata using defuddle with options
        metadata, content = content_extractor.extract_content(
            html_content, 
            url,
            output_format=output_format,
            pipeline_options=pipeline_options
        )
        
        if not content:
            logger.info(f"No content extracted from {url}")
            return False
        
        # For JSON format, save as-is with formatting
        if output_format == 'json':
            try:
                # Parse and re-format for consistency
                json_content = json.loads(content) if isinstance(content, str) else content
                output_data = {
                    'url': url,
                    'metadata': metadata,
                    'content': json_content.get('content', content) if isinstance(json_content, dict) else content
                }
                formatted_content = json.dumps(output_data, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                formatted_content = content
            
            filepath = file_manager.save_file(
                formatted_content, 
                url, 
                extension='json'
            )
        
        # For HTML format, save with metadata header as HTML comment
        elif output_format == 'html':
            header_lines = ['<!--']
            if metadata:
                if metadata.get('title'):
                    header_lines.append(f"Title: {metadata['title']}")
                if metadata.get('description'):
                    header_lines.append(f"Description: {metadata['description']}")
                if metadata.get('author'):
                    header_lines.append(f"Author: {metadata['author']}")
                if metadata.get('date_published'):
                    header_lines.append(f"Published: {metadata['date_published']}")
            header_lines.append('-->')
            header_lines.append('')
            
            html_output = '\n'.join(header_lines) + content
            filepath = file_manager.save_file(
                html_output, 
                url, 
                extension='html'
            )
        
        # For markdown format (default), save with YAML frontmatter
        else:
            # Add metadata header to markdown
            header_lines = ['---']
            if metadata:
                if metadata.get('title'):
                    header_lines.append(f"title: {metadata['title']}")
                if metadata.get('description'):
                    header_lines.append(f"description: {metadata['description']}")
                if metadata.get('author'):
                    header_lines.append(f"author: {metadata['author']}")
                if metadata.get('date_published'):
                    header_lines.append(f"published: {metadata['date_published']}")
                if metadata.get('domain'):
                    header_lines.append(f"domain: {metadata['domain']}")
                if metadata.get('language'):
                    header_lines.append(f"language: {metadata['language']}")
            header_lines.append('---')
            header_lines.append('')
            
            markdown = '\n'.join(header_lines) + content
            filepath = file_manager.save_markdown(markdown, url)
        
        if not filepath:
            logger.info(f"Failed to save content for {url}")
            return False
        
        logger.info(f"Successfully processed {url} -> {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Main entry point of the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Configure logging based on verbosity
    log_level = configure_log_level(args.verbose)
    logger = setup_logging(log_level=log_level)
    
    # Only show these informational messages if verbose mode is enabled
    if args.verbose > 0:
        logger.info(f"Starting extraction from URL: {args.url}")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"Output format: {args.format}")
        logger.info(f"Crawl depth: {args.depth}")
        logger.info(f"Request delay: {args.delay}s")
        logger.info(f"Maximum delay: {args.max_delay}s")
        logger.info(f"Respect robots.txt: {args.respect_robots}")
        logger.info(f"User agent: {args.user_agent}")
        if args.content_selector:
            logger.info(f"Content selector: {args.content_selector}")
    
    # Initialize the session
    session = RateLimitedSession(
        delay=args.delay,
        max_delay=args.max_delay,
        respect_robots=args.respect_robots,
        user_agent=args.user_agent
    )
    
    # Initialize defuddle content extractor
    try:
        content_extractor = DefuddleExtractor(
            node_path=args.node_path, 
            debug=args.verbose >= 2
        )
        if not content_extractor.is_available():
            logger.error("Node.js is required for defuddle but was not found.")
            print("Error: Node.js is required but not found.")
            print("Please install Node.js or provide the path with --node-path")
            sys.exit(1)
        logger.info("Defuddle extractor initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize defuddle extractor: {str(e)}")
        print(f"Error: Failed to initialize defuddle: {str(e)}")
        sys.exit(1)
    
    file_manager = FileManager(output_dir=args.output_dir)
    
    # Try to extract URLs from sitemap first
    logger.info("Attempting to extract URLs from sitemap...")
    urls = extract_sitemap_urls_recursive(session, args.url)
    
    # If sitemap doesn't exist or doesn't have any URLs, fall back to crawling
    if not urls and not args.sitemap_only:
        logger.info("No sitemap found or no URLs in sitemap. Falling back to recursive crawling...")
        crawler = WebCrawler(args.url, session, max_depth=args.depth)
        url_content_map = crawler.crawl()
        urls = list(url_content_map.keys())
    
    if not urls:
        logger.error("No URLs found to process. Check if the site has a sitemap or try changing parameters.")
        print("Error: No URLs found to process.")
        sys.exit(1)
    
    # Build pipeline options from command line arguments
    pipeline_options = {
        'remove_hidden_elements': not args.no_remove_hidden,
        'remove_low_scoring': not args.no_remove_low_scoring,
        'standardize': not args.no_standardize,
        'remove_images': args.remove_images
    }
    
    # Process each URL
    successful = 0
    failed = 0
    logger.info(f"Processing {len(urls)} URLs...")
    
    try:
        with tqdm(total=len(urls), desc="Processing URLs", unit="URL") as progress_bar:
            for url in urls:
                result = process_url(
                    url, 
                    session, 
                    content_extractor, 
                    file_manager,
                    output_format=args.format,
                    pipeline_options=pipeline_options
                )
                if result:
                    successful += 1
                else:
                    failed += 1
                progress_bar.update(1)
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print("\nProcess interrupted by user")
    
    # Report statistics
    logger.info(f"Extraction complete. Successfully processed {successful} URLs.")
    if failed > 0:
        logger.warning(f"Failed to process {failed} URLs.")
    
    print(f"\nExtraction complete.")
    print(f"Successfully processed: {successful} URLs")
    print(f"Failed to process: {failed} URLs")
    print(f"Output directory: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    main()
