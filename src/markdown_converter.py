#!/usr/bin/env python3
"""
Markdown Converter Module

This module provides functionality to convert HTML content to Markdown format.
"""

import logging
from datetime import datetime

import markdownify

logger = logging.getLogger(__name__)


class MarkdownConverter:
    """
    A class that converts HTML content to Markdown.
    """
    
    def __init__(self, heading_style="#", bullets="-"):
        """
        Initialize the Markdown converter.
        
        Args:
            heading_style (str): The style to use for headings (default: "#")
            bullets (str): The style to use for bullet points (default: "-")
        """
        self.heading_style = heading_style
        self.bullets = bullets
    
    def convert_to_markdown(self, html_content, metadata=None):
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: BeautifulSoup object or HTML string
            metadata (dict, optional): Metadata to include in the header
            
        Returns:
            str: Markdown content
        """
        try:
            # Add detailed debugging
            if html_content is None:
                logger.error("HTML content is None")
                return ""
                
            # Check if markdownify is available
            if not markdownify or not hasattr(markdownify, 'markdownify'):
                logger.error("markdownify module is missing or markdownify function is not available")
                return ""
                
            # Convert HTML to Markdown
            logger.debug(f"Converting HTML to Markdown. Content type: {type(html_content)}")
            
            # Convert BeautifulSoup to string if needed
            html_str = str(html_content)
            logger.debug(f"HTML string length: {len(html_str)}")
            
            md = markdownify.markdownify(
                html_str,
                heading_style=self.heading_style,
                bullets=self.bullets
            )
            
            # Clean up the markdown
            md = self._clean_markdown(md)
            
            # Add metadata header if provided
            if metadata:
                md = self._add_metadata_header(md, metadata)
            
            logger.info("Successfully converted HTML to Markdown")
            return md
        
        except Exception as e:
            logger.error(f"Error converting to Markdown: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return ""
    
    def _clean_markdown(self, markdown_content):
        """
        Clean up the generated Markdown to improve readability.
        
        Args:
            markdown_content (str): Markdown content to clean
            
        Returns:
            str: Cleaned Markdown content
        """
        # Replace multiple newlines with at most two
        cleaned = '\n'.join([line for line in markdown_content.splitlines() if line.strip()])
        
        # Ensure there are no more than 2 consecutive newlines
        import re
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Fix spacing around headers
        cleaned = re.sub(r'([^\n])(\n#{1,6} )', r'\1\n\n\2', cleaned)
        
        # Fix spacing after headers
        cleaned = re.sub(r'(#{1,6} .+?)(\n[^#\n])', r'\1\n\2', cleaned)
        
        return cleaned
    
    def _add_metadata_header(self, markdown_content, metadata):
        """
        Add metadata header to the Markdown content.
        
        Args:
            markdown_content (str): Markdown content
            metadata (dict): Metadata to include
            
        Returns:
            str: Markdown content with metadata header
        """
        header_lines = ["---"]
        
        # Add title
        if 'title' in metadata and metadata['title']:
            header_lines.append(f"title: {metadata['title']}")
        
        # Add source URL
        if 'url' in metadata and metadata['url']:
            header_lines.append(f"source_url: {metadata['url']}")
        
        # Add date extracted
        extracted_date = metadata.get('date_extracted', datetime.now().isoformat())
        header_lines.append(f"date_extracted: {extracted_date}")
        
        # Add date published if available
        if 'date_published' in metadata and metadata['date_published']:
            header_lines.append(f"date_published: {metadata['date_published']}")
        
        # Add author if available
        if 'author' in metadata and metadata['author']:
            header_lines.append(f"author: {metadata['author']}")
        
        # Add keywords if available
        if 'keywords' in metadata and metadata['keywords']:
            keywords_str = ', '.join(metadata['keywords'])
            header_lines.append(f"keywords: [{keywords_str}]")
        
        header_lines.append("---")
        
        # Add description as a blockquote if available
        if 'description' in metadata and metadata['description']:
            header_lines.append("")
            header_lines.append(f"> {metadata['description']}")
        
        # Add the original content
        header_lines.append("")
        header_lines.append(markdown_content)
        
        return "\n".join(header_lines)


def convert_html_to_markdown(html_content, metadata=None):
    """
    Convert HTML content to Markdown.
    
    Args:
        html_content: BeautifulSoup object or HTML string
        metadata (dict, optional): Metadata to include in the header
        
    Returns:
        str: Markdown content
    """
    if html_content is None:
        logger.error("Cannot convert None to Markdown")
        return None
    
    converter = MarkdownConverter()
    return converter.convert_to_markdown(html_content, metadata)
