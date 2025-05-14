#!/usr/bin/env python3
"""
Sitemap Parser Module

This module provides functionality to fetch and parse website sitemaps.
"""

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def get_sitemap_url(base_url):
    """
    Construct the possible sitemap URLs for a given base URL.
    
    Args:
        base_url (str): Base URL of the website
        
    Returns:
        list: List of potential sitemap URLs
    """
    # Remove trailing slash if present
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    # Common sitemap locations
    sitemap_paths = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemap/',
        '/sitemap/sitemap.xml',
        '/sitemaps/sitemap.xml',
        '/wp-sitemap.xml',  # Common WordPress sitemap
        '/sitemap-index.xml'  # Another common format
    ]
    
    return [urljoin(base_url, path) for path in sitemap_paths]


def fetch_sitemap(session, base_url):
    """
    Fetch a website's sitemap.
    
    Args:
        session: Session object for making requests
        base_url (str): Base URL of the website
        
    Returns:
        str or None: Content of the sitemap if found, None otherwise
    """
    # First check if the robots.txt has sitemap entries
    robot_sitemaps = []
    if hasattr(session, 'robots_handler'):
        robot_sitemaps = session.robots_handler.get_sitemaps(base_url)
        if robot_sitemaps:
            logger.info(f"Found {len(robot_sitemaps)} sitemaps in robots.txt")
    
    # Try robots.txt sitemaps first, then common locations
    sitemap_urls = robot_sitemaps + get_sitemap_url(base_url)
    
    for sitemap_url in sitemap_urls:
        try:
            logger.info(f"Attempting to fetch sitemap from: {sitemap_url}")
            response = session.get(sitemap_url)
            
            # Check if it seems to be a valid XML file
            content = response.text
            if '<?xml' in content and ('<urlset' in content or '<sitemapindex' in content):
                logger.info(f"Found sitemap at: {sitemap_url}")
                return content
            else:
                logger.debug(f"Found non-XML content at {sitemap_url}")
        
        except Exception as e:
            logger.debug(f"Failed to fetch sitemap from {sitemap_url}: {str(e)}")
    
    logger.warning("No sitemap found")
    return None


def parse_sitemap_urls(sitemap_content):
    """
    Parse URLs from sitemap content.
    
    Args:
        sitemap_content (str): XML content of the sitemap
        
    Returns:
        list: List of URLs found in the sitemap
    """
    urls = []
    
    try:
        soup = BeautifulSoup(sitemap_content, 'xml')
        
        # Check if it's a sitemap index
        is_index = soup.find('sitemapindex') is not None
        
        if is_index:
            # Extract URLs from each sitemap reference
            sitemap_tags = soup.find_all('sitemap')
            logger.info(f"Found sitemap index with {len(sitemap_tags)} sitemaps")
            
            for sitemap_tag in sitemap_tags:
                loc_tag = sitemap_tag.find('loc')
                if loc_tag and loc_tag.string:
                    urls.append(loc_tag.string.strip())
        
        else:
            # Extract URLs from a regular sitemap
            url_tags = soup.find_all('url')
            logger.info(f"Found sitemap with {len(url_tags)} URLs")
            
            for url_tag in url_tags:
                loc_tag = url_tag.find('loc')
                if loc_tag and loc_tag.string:
                    urls.append(loc_tag.string.strip())
    
    except Exception as e:
        logger.error(f"Error parsing sitemap: {str(e)}")
    
    return urls


def extract_sitemap_urls_recursive(session, base_url):
    """
    Recursively extract all URLs from a website's sitemaps.
    
    Args:
        session: Session object for making requests
        base_url (str): Base URL of the website
        
    Returns:
        list: List of all URLs found in the sitemaps
    """
    # Fetch the main sitemap
    sitemap_content = fetch_sitemap(session, base_url)
    if not sitemap_content:
        return []
    
    all_urls = []
    urls_to_process = parse_sitemap_urls(sitemap_content)
    processed_sitemaps = set()
    
    # Process sitemaps recursively
    while urls_to_process:
        url = urls_to_process.pop(0)
        
        # Skip if already processed
        if url in processed_sitemaps:
            continue
        
        processed_sitemaps.add(url)
        
        # Check if it's a sitemap URL (usually ends with .xml)
        if url.endswith('.xml') or 'sitemap' in url.lower():
            try:
                logger.info(f"Fetching nested sitemap: {url}")
                response = session.get(url)
                nested_urls = parse_sitemap_urls(response.text)
                
                # If it returned more sitemap URLs, add them to be processed
                if any(u.endswith('.xml') or 'sitemap' in u.lower() for u in nested_urls):
                    urls_to_process.extend(nested_urls)
                else:
                    # Otherwise, it's a list of content URLs
                    all_urls.extend(nested_urls)
            
            except Exception as e:
                logger.warning(f"Error processing nested sitemap {url}: {str(e)}")
        
        else:
            # It's a content URL, not a sitemap
            all_urls.append(url)
    
    logger.info(f"Extracted {len(all_urls)} URLs from sitemaps")
    return all_urls
