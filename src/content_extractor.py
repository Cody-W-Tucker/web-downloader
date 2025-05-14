#!/usr/bin/env python3
"""
Content Extractor Module

This module provides functionality to extract content and metadata from HTML pages.
"""

import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    A class that extracts content and metadata from HTML pages.
    """
    
    def __init__(self, min_content_length=100):
        """
        Initialize the content extractor.
        
        Args:
            min_content_length (int): Minimum length for extracted content
        """
        self.min_content_length = min_content_length
    
    def extract_metadata(self, soup, url):
        """
        Extract metadata from a BeautifulSoup object.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            url (str): URL of the page
            
        Returns:
            dict: Extracted metadata
        """
        metadata = {
            'url': url,
            'title': self._extract_title(soup),
            'description': self._extract_description(soup),
            'keywords': self._extract_keywords(soup),
            'date_extracted': datetime.now().isoformat(),
            'date_published': self._extract_published_date(soup),
            'author': self._extract_author(soup)
        }
        
        return metadata
    
    def _extract_title(self, soup):
        """
        Extract the title of the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: Page title
        """
        # Try to get title from meta tags first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Fall back to title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Fall back to h1
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.string:
            return h1_tag.get_text(strip=True)
        
        return 'Untitled'
    
    def _extract_description(self, soup):
        """
        Extract the description of the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: Page description
        """
        # Try Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try regular meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        return None
    
    def _extract_keywords(self, soup):
        """
        Extract keywords from the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            list: List of keywords
        """
        keywords = []
        
        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            # Split by comma and strip whitespace
            keywords = [k.strip() for k in meta_keywords['content'].split(',')]
        
        return keywords
    
    def _extract_published_date(self, soup):
        """
        Extract the publication date of the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: Publication date
        """
        # Try common meta tags for publication date
        date_tags = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', property='og:published_time'),
            soup.find('meta', property='published_time'),
            soup.find('meta', itemprop='datePublished')
        ]
        
        for tag in date_tags:
            if tag and tag.get('content'):
                try:
                    return tag['content']
                except Exception:
                    pass
        
        # Try looking for time elements with datetime attribute
        time_tags = soup.find_all('time')
        for tag in time_tags:
            if tag.get('datetime'):
                return tag['datetime']
        
        return None
    
    def _extract_author(self, soup):
        """
        Extract the author of the page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: Author name
        """
        # Try meta tags
        author_tags = [
            soup.find('meta', property='author'),
            soup.find('meta', property='article:author'),
            soup.find('meta', attrs={'name': 'author'}),
            soup.find('meta', itemprop='author')
        ]
        
        for tag in author_tags:
            if tag and tag.get('content'):
                return tag['content'].strip()
        
        # Try common author elements
        author_elements = soup.find_all(['a', 'span', 'div'], class_=re.compile(r'author|byline', re.I))
        for element in author_elements:
            if element.string and 'by' not in element.string.lower():
                return element.get_text(strip=True)
        
        return None
    
    def _is_content_element(self, element):
        """
        Determine if an element is likely to be content.
        
        Args:
            element: A BeautifulSoup element
            
        Returns:
            bool: True if the element is likely to be content
        """
        # Exclude common non-content elements
        if element.name in ['script', 'style', 'nav', 'header', 'footer', 'aside']:
            return False
        
        # Exclude elements with certain classes/IDs
        for attr in ['class', 'id']:
            if not element.has_attr(attr):
                continue
            
            attr_value = element[attr]
            if isinstance(attr_value, list):
                attr_value = ' '.join(attr_value)
            
            if attr_value and any(pattern in attr_value.lower() for pattern in [
                'nav', 'menu', 'sidebar', 'banner', 'ad', 'footer', 'comment', 'related',
                'share', 'social', 'widget', 'popup', 'cookie', 'subscribe'
            ]):
                return False
        
        return True
    
    def extract_main_content(self, soup):
        """
        Extract the main content from a BeautifulSoup object.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            BeautifulSoup: HTML content with non-content elements removed
        """
        if soup is None:
            logger.warning("Cannot extract content from None soup object")
            return None
            
        try:    
            # Try to find article element, which usually contains the main content
            article = soup.find('article')
            if article and len(article.get_text(strip=True)) > self.min_content_length:
                return article
            
            # Try to find content by common IDs/classes
            for selector in ['main', '#content', '.content', '#main', '.main', '.post', '.article']:
                content = soup.select_one(selector)
                if content and len(content.get_text(strip=True)) > self.min_content_length:
                    return content
            
            # If all else fails, try to identify the main content area
            # by finding the element with the most paragraph text
            paragraphs = soup.find_all('p')
            if not paragraphs:
                logger.warning("No paragraphs found in the document")
                # Just return the body as a last resort
                if soup.body:
                    return soup.body
                return soup
            
            # Find common ancestor with most paragraphs
            candidates = {}
            for p in paragraphs:
                # Skip very short paragraphs or those in non-content areas
                if len(p.get_text(strip=True)) < 20:
                    continue
                
                # Walk up the tree to find content containers
                for parent in p.parents:
                    if parent.name == 'body' or parent.name == 'html':
                        break
                    
                    if self._is_content_element(parent):
                        candidates[parent] = candidates.get(parent, 0) + 1
            
            if candidates:
                # Find the candidate with the most paragraphs
                main_content = max(candidates.items(), key=lambda x: x[1])[0]
                if main_content:
                    return main_content
            
            # If we couldn't find a good content area, return the body
            if soup.body:
                logger.debug("Using body as fallback for content")
                return soup.body
                
            # Ultimate fallback
            logger.debug("Using full soup as fallback for content")
            return soup
            
        except Exception as e:
            logger.error(f"Error extracting main content: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Fallback to the body or entire document as a last resort
            if hasattr(soup, 'body') and soup.body:
                return soup.body
            return soup
    
    def clean_content(self, content):
        """
        Clean the extracted content by removing unwanted elements.
        
        Args:
            content (BeautifulSoup): Content to clean
            
        Returns:
            BeautifulSoup: Cleaned content
        """
        if content is None:
            logger.warning("Cannot clean None content")
            return None
        
        try:
            # Instead of using .copy() which might be the issue, create a new BeautifulSoup object
            from copy import copy
            from bs4 import BeautifulSoup
            
            # Convert to string and then parse again to create a deep copy
            content_str = str(content)
            new_content = BeautifulSoup(content_str, 'html.parser')
            
            # Remove script and style elements
            for element in new_content.find_all(['script', 'style', 'iframe', 'noscript']):
                element.decompose()
            
            # Remove hidden elements
            for element in new_content.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden')):
                element.decompose()
            
            # Remove elements with certain classes or IDs
            for element in new_content.find_all(class_=re.compile(r'share|social|comment|ad|sidebar|nav|menu|popup|cookie')):
                element.decompose()
            
            for element in new_content.find_all(id=re.compile(r'share|social|comment|ad|sidebar|nav|menu|popup|cookie')):
                element.decompose()
            
            return new_content
            
        except Exception as e:
            logger.error(f"Error cleaning content: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_content(self, html_content, url):
        """
        Extract content and metadata from HTML.
        
        Args:
            html_content (str): HTML content to extract from
            url (str): URL of the page
            
        Returns:
            tuple: (metadata, content)
        """
        try:
            if not html_content:
                logger.warning(f"No HTML content provided for {url}")
                return None, None
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract metadata
            metadata = self.extract_metadata(soup, url)
            
            # Extract and clean content
            main_content = self.extract_main_content(soup)
            if main_content is None:
                logger.warning(f"Failed to extract main content from {url}")
                return metadata, None
                
            cleaned_content = self.clean_content(main_content)
            if cleaned_content is None:
                logger.warning(f"Failed to clean content from {url}")
                return metadata, None
            
            content_length = len(cleaned_content.get_text(strip=True)) if cleaned_content else 0
            logger.info(f"Extracted content from {url} (size: {content_length} chars)")
            
            return metadata, cleaned_content
        
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None, None
