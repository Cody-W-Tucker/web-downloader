#!/usr/bin/env python3
"""
Web Crawler Module

This module provides functionality to crawl websites, respecting rate limits
and robots.txt directives.
"""

import logging
import random
import time
from collections import deque, defaultdict
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tqdm import tqdm

# Try relative imports (when used as a module)
try:
    from .robots_parser import RobotsHandler, respect_robots_delay
# Fall back to absolute imports (when run directly)
except ImportError:
    from robots_parser import RobotsHandler, respect_robots_delay

logger = logging.getLogger(__name__)


class RateLimitedSession:
    """
    A wrapper around requests.Session that implements rate limiting.
    """
    
    def __init__(self, delay=1.0, max_delay=3.0, respect_robots=True, user_agent=None):
        """
        Initialize the session.
        
        Args:
            delay (float): Minimum delay between requests in seconds
            max_delay (float): Maximum delay for exponential backoff
            respect_robots (bool): Whether to respect robots.txt
            user_agent (str): User agent string to use
        """
        self.session = requests.Session()
        self.delay = delay
        self.max_delay = max_delay
        self.last_request_time = defaultdict(float)  # time of last request per domain
        self.respect_robots = respect_robots
        
        # Set up user agent
        if user_agent:
            self.user_agent = user_agent
        else:
            try:
                ua = UserAgent()
                self.user_agent = ua.chrome
            except Exception:
                self.user_agent = "WebToMarkdown/1.0"
        
        self.session.headers.update({"User-Agent": self.user_agent})
        
        # Initialize robots handler if needed
        if self.respect_robots:
            self.robots_handler = RobotsHandler(self.user_agent)
    
    def _get_domain(self, url):
        """
        Extract domain from URL.
        
        Args:
            url (str): URL to extract domain from
            
        Returns:
            str: Domain name
        """
        return urlparse(url).netloc
    
    def _wait_for_rate_limit(self, url):
        """
        Wait to respect rate limits for the domain.
        
        Args:
            url (str): URL to get domain from
        """
        domain = self._get_domain(url)
        elapsed = time.time() - self.last_request_time[domain]
        
        if elapsed < self.delay:
            # Add some randomization to avoid detection
            wait_time = self.delay - elapsed + random.uniform(0, 0.5)
            logger.debug(f"Rate limiting: Waiting {wait_time:.2f}s before request to {domain}")
            time.sleep(wait_time)
    
    @respect_robots_delay
    def get(self, url, **kwargs):
        """
        Perform a GET request with rate limiting.
        
        Args:
            url (str): URL to request
            **kwargs: Additional arguments to pass to requests.get
            
        Returns:
            requests.Response: Response object
        """
        # Check robots.txt if enabled
        if self.respect_robots and not self.robots_handler.can_fetch(url):
            raise PermissionError(f"Access to {url} disallowed by robots.txt")
        
        # Apply rate limiting
        self._wait_for_rate_limit(url)
        
        # Record time before making the request
        domain = self._get_domain(url)
        self.last_request_time[domain] = time.time()
        
        try:
            logger.debug(f"Requesting: {url}")
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Error requesting {url}: {str(e)}")
            
            # Implement exponential backoff for server errors
            if hasattr(e.response, 'status_code') and 500 <= e.response.status_code < 600:
                backoff_time = min(self.delay * 2, self.max_delay) * random.uniform(0.8, 1.2)
                logger.info(f"Server error, backing off for {backoff_time:.2f}s")
                time.sleep(backoff_time)
            
            raise


def normalize_url(base_url, url):
    """
    Normalize a URL: resolve relative URLs, remove fragments, etc.
    
    Args:
        base_url (str): Base URL for resolving relative URLs
        url (str): URL to normalize
        
    Returns:
        str: Normalized URL
    """
    # Join with base URL if it's a relative URL
    absolute_url = urljoin(base_url, url)
    
    # Remove fragment identifier
    url_without_fragment = urldefrag(absolute_url)[0]
    
    # Parse the URL
    parsed = urlparse(url_without_fragment)
    
    # Reconstruct the URL without query parameters if they're not meaningful
    # This is a basic example - you might want to keep some query parameters based on your needs
    if parsed.path.endswith(('.html', '.htm', '.php', '.asp', '.aspx', '.jsp')):
        # For content pages, we might want to keep query parameters
        return url_without_fragment
    elif not parsed.path or parsed.path.endswith('/'):
        # For directory-like URLs, we might want to keep query parameters
        return url_without_fragment
    else:
        # For other URLs, strip the query parameters
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def is_internal_url(base_url, url):
    """
    Check if a URL is internal (same domain as base_url).
    
    Args:
        base_url (str): Base URL to compare against
        url (str): URL to check
        
    Returns:
        bool: True if the URL is internal, False otherwise
    """
    base_domain = urlparse(base_url).netloc
    url_domain = urlparse(url).netloc
    
    # Check if the URL is relative or has the same domain
    return not url_domain or url_domain == base_domain


def is_valid_url(url):
    """
    Check if a URL is valid for crawling.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    parsed = urlparse(url)
    
    # Check if it's an HTTP(S) URL
    if parsed.scheme not in ('http', 'https'):
        return False
    
    # Skip mail links, tel links, etc.
    if parsed.scheme in ('mailto', 'tel', 'ftp', 'javascript'):
        return False
    
    # Skip common file extensions that are not web pages
    if parsed.path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', 
                            '.xls', '.xlsx', '.zip', '.tar.gz', '.exe', '.dmg')):
        return False
    
    return True


class WebCrawler:
    """
    A class that crawls websites and extracts content.
    """
    
    def __init__(self, base_url, session, max_depth=5):
        """
        Initialize the crawler.
        
        Args:
            base_url (str): Base URL to start crawling from
            session (RateLimitedSession): Session to use for requests
            max_depth (int): Maximum recursion depth
        """
        self.base_url = base_url
        self.session = session
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_content = {}  # Maps URLs to their HTML content
    
    def extract_links(self, url, html_content):
        """
        Extract links from HTML content.
        
        Args:
            url (str): URL of the page
            html_content (str): HTML content to extract links from
            
        Returns:
            list: List of extracted links
        """
        links = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip empty links, anchors, and javascript
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Normalize the URL
            normalized_url = normalize_url(url, href)
            
            # Check if it's an internal URL and valid
            if is_internal_url(self.base_url, normalized_url) and is_valid_url(normalized_url):
                links.append(normalized_url)
        
        return links
    
    def crawl_url(self, url):
        """
        Crawl a single URL and extract its content.
        
        Args:
            url (str): URL to crawl
            
        Returns:
            tuple: (HTML content, list of links)
        """
        try:
            response = self.session.get(url)
            html_content = response.text
            links = self.extract_links(url, html_content)
            self.url_content[url] = html_content
            logger.info(f"Crawled: {url} - Found {len(links)} links")
            return html_content, links
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            return None, []
    
    def crawl(self):
        """
        Crawl the website starting from the base URL.
        
        Returns:
            dict: Dictionary mapping URLs to their HTML content
        """
        queue = deque([(self.base_url, 0)])  # (url, depth)
        
        while queue:
            url, depth = queue.popleft()
            
            # Skip if already visited or depth exceeded
            if url in self.visited_urls or depth > self.max_depth:
                continue
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Crawl the URL
            _, links = self.crawl_url(url)
            
            # Add new links to the queue
            for link in links:
                if link not in self.visited_urls:
                    queue.append((link, depth + 1))
        
        return self.url_content
