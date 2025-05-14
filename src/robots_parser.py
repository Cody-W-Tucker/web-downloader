#!/usr/bin/env python3
"""
Robots.txt Parser Module

This module provides functionality to parse and respect robots.txt directives.
"""

import logging
import time
import urllib.robotparser
import urllib.request
import urllib.error
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class RobotsHandler:
    """
    A class that handles robots.txt parsing and checking.
    """
    
    def __init__(self, user_agent, default_403_policy='allow'):
        """
        Initialize the RobotsHandler.
        
        Args:
            user_agent (str): The user agent string to use for requests
            default_403_policy (str): Policy for handling 403 errors when accessing robots.txt
                                     'allow' - Allow all paths with a warning
                                     'conservative' - Block all paths except common ones
        """
        self.user_agent = user_agent
        self.default_403_policy = default_403_policy
        self.parsers = {}  # Cache of RobotFileParser objects, keyed by domain
        self.crawl_delays = {}  # Cache of crawl delays, keyed by domain
        self.denied_robots = set()  # Set of domains that denied access to robots.txt
    
    def get_parser_for_url(self, url):
        """
        Get or create a parser for the domain of the given URL.
        
        Args:
            url (str): The URL to get a parser for
            
        Returns:
            urllib.robotparser.RobotFileParser: The parser for the domain
        """
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if domain not in self.parsers:
            logger.info(f"Initializing robots.txt parser for domain: {domain}")
            parser = urllib.robotparser.RobotFileParser()
            robots_url = f"{domain}/robots.txt"
            
            # Create a custom parser with a proper user agent first
            try:
                logger.debug(f"Attempting to fetch robots.txt from {robots_url} with user agent: {self.user_agent}")
                
                # Create a proper request with browser-like headers
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'text/plain,text/html;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive',
                }
                request = urllib.request.Request(robots_url, headers=headers)
                
                # Attempt to fetch the robots.txt file
                try:
                    with urllib.request.urlopen(request) as response:
                        robots_content = response.read().decode('utf-8', errors='replace')
                        logger.debug(f"Successfully fetched robots.txt from {domain}!")
                        logger.debug(f"Response headers: {dict(response.headers)}")
                        logger.debug(f"Robots.txt content from {domain}:\n{robots_content}")
                        
                        # Manually parse the robots.txt content
                        parser.parse(robots_content.splitlines())
                        self.parsers[domain] = parser
                        
                        # Try to get crawl delay
                        crawl_delay = parser.crawl_delay(self.user_agent)
                        if crawl_delay:
                            logger.info(f"Found crawl delay of {crawl_delay}s for {domain}")
                            self.crawl_delays[domain] = crawl_delay
                        
                        # Log the site's sitemap if present
                        if hasattr(parser, 'sitemaps') and parser.sitemaps:
                            for sitemap in parser.sitemaps:
                                logger.info(f"Found sitemap in robots.txt: {sitemap}")
                        
                        return parser
                        
                except urllib.error.HTTPError as e:
                    logger.warning(f"HTTP error {e.code} fetching robots.txt from {domain}: {str(e)}")
                    logger.debug(f"Response headers: {dict(e.headers) if hasattr(e, 'headers') else 'No headers'}")
                    
                    if e.code == 403:
                        # Special handling for 403 Forbidden errors
                        self.denied_robots.add(domain)
                        logger.warning(f"Access to robots.txt forbidden (403) for {domain}. Using {self.default_403_policy} policy.")
                        
                        # Attempt with standard urllib method as fallback
                        parser.set_url(robots_url)
                        try:
                            parser.read()
                            self.parsers[domain] = parser
                            return parser
                        except:
                            # Create an appropriate parser based on policy
                            empty_parser = urllib.robotparser.RobotFileParser()
                            if self.default_403_policy == 'allow':
                                # Allow everything by default
                                empty_parser.parse(['User-agent: *', 'Allow: /'])
                            else:  # conservative policy
                                # Only allow common public paths, block everything else
                                empty_parser.parse([
                                    'User-agent: *',
                                    'Allow: /$',  # Root path only
                                    'Allow: /index.html$',
                                    'Allow: /index.php$',
                                    'Allow: /sitemap.xml$',
                                    'Allow: /robots.txt$',
                                    'Disallow: /'  # Block everything else
                                ])
                            self.parsers[domain] = empty_parser
                            return empty_parser
                    else:
                        raise  # Re-raise other HTTP errors
                
                except Exception as e:
                    logger.warning(f"Error fetching robots.txt from {domain}: {str(e)}")
                    # Fall through to standard method as backup
                    
                # If custom approach failed, try standard urllib method as fallback
                parser.set_url(robots_url)
                try:
                    parser.read()
                    self.parsers[domain] = parser
                except Exception as e:
                    logger.warning(f"Error reading robots.txt with standard method from {domain}: {str(e)}")
                    # Create an empty parser in permissive mode to avoid repeated failures
                    empty_parser = urllib.robotparser.RobotFileParser()
                    # Set an empty ruleset that allows everything by default
                    empty_parser.parse(['User-agent: *', 'Allow: /'])
                    self.parsers[domain] = empty_parser
            
            except Exception as general_e:
                logger.warning(f"Unexpected error handling robots.txt for {domain}: {str(general_e)}")
                # Create an empty parser in permissive mode
                empty_parser = urllib.robotparser.RobotFileParser()
                empty_parser.parse(['User-agent: *', 'Allow: /'])
                self.parsers[domain] = empty_parser
        
        return self.parsers[domain]
    
    def can_fetch(self, url):
        """
        Check if the URL can be fetched according to robots.txt rules.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL can be fetched, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            path = parsed_url.path
            
            # Special handling for domains that denied robots.txt access
            if domain in self.denied_robots:
                # For 'allow' policy, all paths are allowed
                if self.default_403_policy == 'allow':
                    logger.debug(f"Access allowed by {self.default_403_policy} policy for {url}")
                    return True
                
                # For conservative policy, only allow specific paths
                if path in ['/', '/index.html', '/index.php', '/sitemap.xml', '/robots.txt'] or path == '':
                    logger.debug(f"Access to common path allowed despite 403 robots.txt: {url}")
                    return True
                
                # Block for non-allowed paths in conservative mode
                logger.warning(f"Access denied by {self.default_403_policy} policy for {url}")
                return False
            
            # Normal robots.txt handling
            parser = self.get_parser_for_url(url)
            
            # Special handling for sitemaps explicitly mentioned in robots.txt
            if hasattr(parser, 'sitemaps') and parser.sitemaps:
                for sitemap in parser.sitemaps:
                    if url == sitemap:
                        logger.info(f"Explicitly allowing sitemap from robots.txt: {url}")
                        return True
            
            # Regular permission check
            result = parser.can_fetch(self.user_agent, url)
            
            if result:
                logger.debug(f"Allowed by robots.txt: {url}")
            else:
                # Log more details for debugging
                logger.warning(f"Disallowed by robots.txt: {url}")
                logger.debug(f"Path being checked: {path}")
                
                # Check if it's a common sitemap URL - these should generally be allowed
                common_sitemaps = [
                    '/sitemap.xml', 
                    '/wp-sitemap.xml', 
                    '/sitemap_index.xml'
                ]
                if any(path.endswith(sitemap) for sitemap in common_sitemaps):
                    logger.warning(f"Allowing common sitemap URL despite robots.txt: {url}")
                    return True
                
                # For root paths, double-check the denial
                if path == '/' or path == '':
                    logger.warning(f"Root path disallowed by robots.txt parser, but this may be a parser error: {url}")
                    return True
            
            return result
        
        except Exception as e:
            logger.warning(f"Error checking robots.txt permission for {url}: {str(e)}")
            # Default to allowing access if there's an error
            return True
    
    def get_crawl_delay(self, url):
        """
        Get the crawl delay for the domain of the given URL.
        
        Args:
            url (str): The URL to get the crawl delay for
            
        Returns:
            float: The crawl delay in seconds, or None if not specified
        """
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # For domains with 403 robots.txt, use a default crawl delay
        if domain in self.denied_robots:
            return 10.0  # Conservative default
        
        # Ensure parser has been initialized
        self.get_parser_for_url(url)
        
        return self.crawl_delays.get(domain)
    
    def get_sitemaps(self, url):
        """
        Get list of sitemaps defined in robots.txt for the domain.
        
        Args:
            url (str): The URL to get sitemaps for
            
        Returns:
            list: List of sitemap URLs, or empty list if none found
        """
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # For domains with 403 robots.txt, suggest common sitemap locations
        if domain in self.denied_robots:
            return [
                f"{domain}/sitemap.xml",
                f"{domain}/wp-sitemap.xml",
                f"{domain}/sitemap_index.xml"
            ]
        
        parser = self.get_parser_for_url(url)
        
        if hasattr(parser, 'sitemaps') and parser.sitemaps:
            return parser.sitemaps
        
        return []


def respect_robots_delay(func):
    """
    Decorator to respect robots.txt crawl delay directives.
    
    Args:
        func: The function to decorate
        
    Returns:
        wrapper: The decorated function
    """
    def wrapper(self, url, *args, **kwargs):
        if not self.respect_robots:
            return func(self, url, *args, **kwargs)
        
        robots_handler = self.robots_handler
        crawl_delay = robots_handler.get_crawl_delay(url)
        
        if crawl_delay:
            # Use the robots.txt crawl delay
            time.sleep(crawl_delay)
        
        return func(self, url, *args, **kwargs)
    
    return wrapper
