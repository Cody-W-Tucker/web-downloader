#!/usr/bin/env python3
"""
File Manager Module

This module provides functionality to manage file operations like saving Markdown files.
"""

import logging
import os
import re
import yaml
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FileManager:
    """
    A class that manages file operations.
    
    When used with a domain-based output directory (the default approach),
    files will be saved using the original URL path structure inside
    the specified domain directory.
    """
    
    def __init__(self, output_dir="output"):
        """
        Initialize the file manager.
        
        Args:
            output_dir (str): Directory to save output files.
                              Usually set to the domain name by the wrapper script.
        """
        self.output_dir = output_dir
        self._create_directory(output_dir)
        
        # Check if output_dir is already domain-based
        # This avoids creating nested domain directories
        self.output_is_domain_based = output_dir.startswith('./') and '/' not in output_dir[2:] and '\\' not in output_dir[2:]
    
    def _create_directory(self, directory):
        """
        Create a directory if it doesn't exist.
        
        Args:
            directory (str): Directory path
            
        Returns:
            bool: True if directory exists or was created, False otherwise
        """
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")
            return False
    
    def url_to_filepath(self, url):
        """
        Convert a URL to a file path.
        
        Args:
            url (str): URL to convert
            
        Returns:
            tuple: (directory_path, filename)
        """
        parsed_url = urlparse(url)
        
        # Get the domain
        domain = parsed_url.netloc
        
        # Remove www. prefix if present
        domain = re.sub(r'^www\.', '', domain)
        
        # Get the path and remove trailing slash
        path = parsed_url.path
        if path.endswith('/'):
            path = path[:-1]
        
        # Handle empty path (root URL)
        if not path:
            path = '/index'
        
        # Split path into components
        path_components = path.split('/')
        
        # Convert the last component to a filename
        filename = path_components[-1]
        
        # Handle query parameters if necessary
        if parsed_url.query:
            # Use only the first few chars of the query to avoid overly long filenames
            query_hash = parsed_url.query[:20]
            filename = f"{filename}_{query_hash}"
        
        # Sanitize the filename
        filename = self._sanitize_filename(filename)
        
        # Ensure it has a .md extension
        if not filename.endswith('.md'):
            filename = f"{filename}.md"
        
        # Determine directory structure
        if self.output_is_domain_based:
            # If output_dir is already domain-based, don't include domain in the path
            dir_components = path_components[:-1]
        else:
            # Include domain in path if output_dir is not domain-based
            dir_components = [domain] + path_components[:-1]
        
        # Build the full directory path
        directory = os.path.join(self.output_dir, *dir_components) if dir_components else self.output_dir
        
        return directory, filename
    
    def _sanitize_filename(self, filename):
        """
        Sanitize a filename to make it filesystem-safe.
        
        Args:
            filename (str): Filename to sanitize
            
        Returns:
            str: Sanitized filename
        """
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        
        # Handle dots and spaces
        sanitized = sanitized.replace(' ', '_')
        
        # Handle cases where the filename might still be invalid
        if not sanitized or sanitized in ('.', '..'):
            sanitized = 'index'
        
        # Handle non-ASCII characters if needed
        sanitized = ''.join(c for c in sanitized if c.isascii() or c.isalnum() or c in '-_.')
        
        # Truncate if too long (most filesystems have limits)
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        return sanitized
    
    def _normalize_url(self, url):
        """
        Normalize a URL by removing trailing slashes and normalizing the domain.
        
        Args:
            url (str): URL to normalize
            
        Returns:
            str: Normalized URL
        """
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Normalize www. prefix
        url = re.sub(r'(https?://)www\.', r'\1', url)
        
        return url
    
    def _extract_frontmatter(self, content):
        """
        Extract frontmatter from markdown content.
        
        Args:
            content (str): Markdown content with potential frontmatter
            
        Returns:
            tuple: (frontmatter_dict, content_without_frontmatter) or (None, content) if no frontmatter
        """
        if content.startswith('---\n'):
            # Find the end of frontmatter
            end_pos = content.find('\n---\n', 4)
            if end_pos != -1:
                frontmatter_str = content[4:end_pos]
                try:
                    frontmatter = yaml.safe_load(frontmatter_str)
                    content_without_frontmatter = content[end_pos + 5:]
                    return frontmatter, content_without_frontmatter
                except yaml.YAMLError:
                    # Invalid YAML, treat as if there's no frontmatter
                    pass
        
        return None, content
    
    def _add_frontmatter(self, content, url, title=None):
        """
        Add frontmatter to markdown content.
        
        Args:
            content (str): Original markdown content
            url (str): Source URL
            title (str, optional): Page title. If None, try to extract from content
            
        Returns:
            str: Markdown content with frontmatter
        """
        # Strip any existing frontmatter
        _, cleaned_content = self._extract_frontmatter(content)
        
        # Try to extract title from content if not provided
        if title is None:
            # Look for first heading
            heading_match = re.search(r'^# (.+)$', cleaned_content, re.MULTILINE)
            if heading_match:
                title = heading_match.group(1).strip()
            else:
                # Fallback to using the last part of the URL path
                parsed_url = urlparse(url)
                path_parts = parsed_url.path.rstrip('/').split('/')
                title = path_parts[-1] if path_parts and path_parts[-1] else 'Home Page'
                # Convert dashes and underscores to spaces and capitalize
                title = ' '.join(word.capitalize() for word in re.split(r'[-_]', title))
        
        # Create frontmatter
        frontmatter = {
            'title': title,
            'source_url': url,
            'date_extracted': datetime.now().isoformat()
        }
        
        # Convert to YAML
        frontmatter_str = yaml.dump(frontmatter, default_flow_style=False)
        
        # Combine with content
        return f"---\n{frontmatter_str}---\n\n{cleaned_content.lstrip()}"
    
    def save_markdown(self, markdown_content, url, title=None):
        """
        Save Markdown content to a file based on the URL structure.
        Adds frontmatter with metadata.
        
        Args:
            markdown_content (str): Markdown content to save
            url (str): URL of the source
            title (str, optional): Page title. If None, try to extract from content
            
        Returns:
            str: Path to the saved file, or None if failed
        """
        try:
            directory, filename = self.url_to_filepath(url)
            
            # Create the directory structure
            if not self._create_directory(directory):
                return None
            
            # Full path to the file
            filepath = os.path.join(directory, filename)
            
            # Add frontmatter
            content_with_frontmatter = self._add_frontmatter(markdown_content, url, title)
            
            # Handle naming conflicts
            filepath = self._handle_naming_conflict(filepath, url, content_with_frontmatter)
            
            # Write the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_with_frontmatter)
            
            logger.info(f"Saved Markdown file: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving Markdown for {url}: {str(e)}")
            return None
    
    def _handle_naming_conflict(self, filepath, url, content_with_frontmatter):
        """
        Handle naming conflicts by checking if the existing file is from the same URL.
        If it's the same URL, update the file. Otherwise, append a number to the filename.
        
        Args:
            filepath (str): Original filepath
            url (str): Source URL of the new content
            content_with_frontmatter (str): New content with frontmatter
            
        Returns:
            str: Modified filepath if needed, or original filepath
        """
        if not os.path.exists(filepath):
            return filepath
        
        # Normalize the new URL
        normalized_new_url = self._normalize_url(url)
        
        try:
            # Read existing file
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            # Extract frontmatter
            existing_frontmatter, _ = self._extract_frontmatter(existing_content)
            
            # If there's frontmatter and the source URL matches (ignoring trailing slashes)
            if (existing_frontmatter and 'source_url' in existing_frontmatter and 
                self._normalize_url(existing_frontmatter['source_url']) == normalized_new_url):
                # It's an update to the same page, just overwrite
                logger.debug(f"Updating existing file {filepath} from same URL")
                return filepath
        except Exception as e:
            logger.warning(f"Error reading existing file {filepath}: {str(e)}")
        
        # If we reach here, it's a different page with a name conflict
        base, ext = os.path.splitext(filepath)
        counter = 1
        
        while True:
            new_filepath = f"{base}_{counter}{ext}"
            if not os.path.exists(new_filepath):
                logger.debug(f"Renamed {filepath} to {new_filepath} to avoid conflict with different content")
                return new_filepath
            
            # Check if this numbered version is from the same URL
            try:
                with open(new_filepath, 'r', encoding='utf-8') as f:
                    numbered_content = f.read()
                
                numbered_frontmatter, _ = self._extract_frontmatter(numbered_content)
                
                if (numbered_frontmatter and 'source_url' in numbered_frontmatter and 
                    self._normalize_url(numbered_frontmatter['source_url']) == normalized_new_url):
                    # Found a match with an existing numbered version, update it
                    logger.debug(f"Updating existing numbered file {new_filepath} from same URL")
                    return new_filepath
            except Exception:
                pass
            
            counter += 1
