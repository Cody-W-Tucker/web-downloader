#!/usr/bin/env python3
"""
Defuddle Content Extractor Module

This module provides a content extractor that uses defuddle
(a better HTML parser) to extract content from web pages.

It calls the defuddle Node.js wrapper script to process HTML content.

Full defuddle feature support:
  - Output formats: HTML, Markdown, JSON
  - All metadata extraction (author, title, description, etc.)
  - Debug mode with detailed extraction info
  - Content selector override
  - Pipeline toggles for fine-tuned extraction
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Optional, Tuple, Dict, Any, Union

logger = logging.getLogger(__name__)


class DefuddleExtractor:
    """
    A class that extracts content using defuddle via a Node.js wrapper.
    
    Supports full defuddle API with all options and output formats.
    """
    
    def __init__(self, node_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the defuddle extractor.
        
        Args:
            node_path: Path to the node executable (optional, will try to find it)
            debug: Enable debug mode for verbose output
        """
        self.debug = debug
        self.node_path = node_path or self._find_node()
        self.wrapper_path = self._find_wrapper()
        
    def _find_node(self) -> str:
        """Find the node executable."""
        # Try common paths and commands
        for cmd in ['node', 'nodejs']:
            try:
                result = subprocess.run(
                    ['which', cmd],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        # Check common installation paths
        for path in ['/usr/bin/node', '/usr/local/bin/node', '/opt/node/bin/node']:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
                
        # If we're in a nix-shell environment
        nix_node = os.environ.get('NIX_NODE_PATH')
        if nix_node and os.path.isfile(nix_node):
            return nix_node
            
        raise RuntimeError(
            "Could not find node executable. Please ensure Node.js is installed "
            "or provide the path via the node_path parameter."
        )
    
    def _find_wrapper(self) -> str:
        """Find the defuddle wrapper script."""
        # First check for environment variable (used by nix wrapper)
        env_path = os.environ.get('DEFUDDLE_WRAPPER')
        if env_path and os.path.isfile(env_path):
            return env_path
        
        # Look for the wrapper in the same directory as this module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        wrapper_path = os.path.join(module_dir, 'defuddle_wrapper.js')
        
        if os.path.isfile(wrapper_path):
            return wrapper_path
        
        # Try the project root (development mode)
        project_root = os.path.dirname(module_dir)
        wrapper_path = os.path.join(project_root, 'src', 'defuddle_wrapper.js')
        
        if os.path.isfile(wrapper_path):
            return wrapper_path
            
        raise RuntimeError(
            f"Could not find defuddle_wrapper.js. Searched in: {module_dir}, {project_root}/src/"
        )

    def _build_command(
        self,
        url: str,
        output_format: str = 'markdown',
        property_name: Optional[str] = None,
        content_selector: Optional[str] = None,
        pipeline_options: Optional[Dict[str, bool]] = None,
    ) -> list[str]:
        """Build the defuddle wrapper command for a request."""
        cmd = [
            self.node_path,
            self.wrapper_path,
            '--url', url,
            '--format', output_format
        ]

        if self.debug:
            cmd.append('--debug')

        if property_name:
            cmd.extend(['--property', property_name])

        if content_selector:
            cmd.extend(['--content-selector', content_selector])

        pipeline_defaults = {
            'remove_exact_selectors': True,
            'remove_partial_selectors': True,
            'remove_hidden_elements': True,
            'remove_low_scoring': True,
            'remove_small_images': True,
            'remove_images': False,
            'standardize': True,
            'use_async': True
        }

        if pipeline_options:
            pipeline_defaults.update(pipeline_options)

        if not pipeline_defaults['remove_exact_selectors']:
            cmd.append('--no-remove-exact')
        if not pipeline_defaults['remove_partial_selectors']:
            cmd.append('--no-remove-partial')
        if not pipeline_defaults['remove_hidden_elements']:
            cmd.append('--no-remove-hidden')
        if not pipeline_defaults['remove_low_scoring']:
            cmd.append('--no-remove-low-scoring')
        if not pipeline_defaults['remove_small_images']:
            cmd.append('--no-remove-small-images')
        if pipeline_defaults['remove_images']:
            cmd.append('--remove-images')
        if not pipeline_defaults['standardize']:
            cmd.append('--no-standardize')
        if not pipeline_defaults['use_async']:
            cmd.append('--no-async')

        return cmd

    def extract_raw_content(
        self,
        html_content: str,
        url: str,
        output_format: str = 'markdown',
        property_name: Optional[str] = None,
        content_selector: Optional[str] = None,
        pipeline_options: Optional[Dict[str, bool]] = None,
    ) -> Optional[str]:
        """Run defuddle and return the raw wrapper output."""
        try:
            if not html_content or not html_content.strip():
                logger.warning(f"No HTML content provided for {url}")
                return None

            cmd = self._build_command(
                url,
                output_format=output_format,
                property_name=property_name,
                content_selector=content_selector,
                pipeline_options=pipeline_options,
            )

            logger.debug(f"Running defuddle extractor for {url} with format: {output_format}")

            result = subprocess.run(
                cmd,
                input=html_content,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Defuddle extractor failed for {url}: {result.stderr}")
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"Defuddle extractor timed out for {url}")
            return None
        except Exception as e:
            logger.error(f"Error extracting content with defuddle for {url}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_content(
        self, 
        html_content: str, 
        url: str,
        output_format: str = 'markdown',
        property_name: Optional[str] = None,
        content_selector: Optional[str] = None,
        pipeline_options: Optional[Dict[str, bool]] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Extract content and metadata from HTML using defuddle.
        
        Args:
            html_content: The HTML content to parse
            url: The URL of the page (used for resolving relative links and metadata)
            output_format: Output format - 'html', 'markdown', or 'json'
            property_name: Extract only a specific property (e.g., 'title', 'author')
            content_selector: CSS selector to use as main content element
            pipeline_options: Dict of pipeline toggle options:
                - remove_exact_selectors (default: True)
                - remove_partial_selectors (default: True)
                - remove_hidden_elements (default: True)
                - remove_low_scoring (default: True)
                - remove_small_images (default: True)
                - remove_images (default: False)
                - standardize (default: True)
                - use_async (default: True)
            
        Returns:
            Tuple of (metadata dict, content string). 
            For JSON format, content contains the full JSON response.
            Returns (None, None) on failure.
        """
        try:
            result_stdout = self.extract_raw_content(
                html_content,
                url,
                output_format=output_format,
                property_name=property_name,
                content_selector=content_selector,
                pipeline_options=pipeline_options,
            )

            if result_stdout is None:
                return None, None
            
            # Handle property extraction (returns plain text, not JSON)
            if property_name:
                return None, result_stdout.strip()
            
            # Parse the JSON output (for json format)
            if output_format == 'json':
                try:
                    output = json.loads(result_stdout)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse defuddle output for {url}: {e}")
                    logger.debug(f"Raw output: {result_stdout[:500]}")
                    return None, None

                if not isinstance(output, dict):
                    logger.error(f"Defuddle extraction returned non-object JSON for {url}")
                    return None, None

                # Return full output as metadata, and content separately
                content = output.get('content', '')

                # Remove content from metadata to avoid duplication
                metadata = {k: v for k, v in output.items() if k not in {'content', 'success'}}

                return metadata, content
            
            try:
                output = json.loads(result_stdout)

                if not isinstance(output, dict):
                    logger.error(f"Defuddle extraction returned non-object JSON for {url}")
                    return None, None

                # Extract metadata
                metadata = {
                    'url': output.get('url', url),
                    'title': output.get('title', 'Untitled'),
                    'description': output.get('description'),
                    'author': output.get('author'),
                    'date_published': output.get('published'),
                    'domain': output.get('domain'),
                    'site': output.get('site'),
                    'language': output.get('language'),
                    'word_count': output.get('wordCount'),
                    'parse_time': output.get('parseTime'),
                    'favicon': output.get('favicon'),
                    'image': output.get('image'),
                    'meta_tags': output.get('metaTags'),
                    'schema_org_data': output.get('schemaOrgData')
                }
                
                content = output.get('content', '')
                
                if not content:
                    logger.warning(f"No content extracted from {url}")
                    return metadata, None
                
                content_length = len(content)
                logger.info(f"Defuddle extracted content from {url} (size: {content_length} chars, {output.get('wordCount', 0)} words)")
                
                if self.debug and output.get('debug'):
                    logger.debug(f"Defuddle debug info for {url}: {output['debug']}")
                
                return metadata, content
                
            except json.JSONDecodeError:
                # If output is not JSON, treat it as raw content
                content = result_stdout
                return {'url': url}, content
        except Exception as e:
            logger.error(f"Error extracting content with defuddle for {url}: {str(e)}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None, None
    
    def extract_metadata(self, html_content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract only metadata from HTML using defuddle.
        
        Args:
            html_content: The HTML content to parse
            url: The URL of the page
            
        Returns:
            Dictionary of metadata or None on failure
        """
        metadata, _ = self.extract_content(html_content, url, output_format='json')
        return metadata
    
    def extract_single_property(self, html_content: str, url: str, property_name: str) -> Optional[str]:
        """
        Extract a single property from HTML using defuddle.
        
        Args:
            html_content: The HTML content to parse
            url: The URL of the page
            property_name: Name of the property to extract (e.g., 'title', 'author')
            
        Returns:
            Property value as string or None on failure
        """
        _, content = self.extract_content(
            html_content, 
            url, 
            output_format='json',
            property_name=property_name
        )
        return content
    
    def is_available(self) -> bool:
        """Check if defuddle is available and working."""
        try:
            # Test by running with --help equivalent (just check if node and wrapper exist)
            result = subprocess.run(
                [self.node_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


# Convenience function for direct usage
def extract_with_defuddle(
    html_content: str, 
    url: str, 
    output_format: str = 'markdown',
    node_path: Optional[str] = None, 
    debug: bool = False,
    **kwargs
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Extract content from HTML using defuddle.
    
    Args:
        html_content: The HTML content to parse
        url: The URL of the page
        output_format: Output format - 'html', 'markdown', or 'json'
        node_path: Optional path to node executable
        debug: Enable debug mode
        **kwargs: Additional options passed to DefuddleExtractor.extract_content()
        
    Returns:
        Tuple of (metadata dict, content string)
    """
    extractor = DefuddleExtractor(node_path=node_path, debug=debug)
    return extractor.extract_content(html_content, url, output_format=output_format, **kwargs)


def extract_metadata(html_content: str, url: str, node_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract only metadata from HTML using defuddle.
    
    Args:
        html_content: The HTML content to parse
        url: The URL of the page
        node_path: Optional path to node executable
        
    Returns:
        Dictionary of metadata or None on failure
    """
    extractor = DefuddleExtractor(node_path=node_path)
    return extractor.extract_metadata(html_content, url)
