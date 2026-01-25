# Agent Guidelines for web-downloader

This document provides coding guidelines and commands for agentic coding assistants working on the web-downloader project.

## Project Overview

web-downloader is a Python CLI tool that extracts content from websites and downloads YouTube transcripts, converting everything to clean Markdown format. It uses Python 3.13, mypy for type checking, ruff for linting, and pytest for testing.

## Build, Lint, and Test Commands

### Type Checking
```bash
# Check types for the entire codebase
mypy src tests

# Check types for a specific file
mypy src/main.py
```

### Linting
```bash
# Lint the entire codebase
ruff check src tests

# Lint a specific file
ruff check src/main.py

# Auto-fix linting issues where possible
ruff check --fix src tests

# Format code
ruff format src tests
```

### Testing
```bash
# Run all tests
pytest tests

# Run tests for a specific file
pytest tests/test_youtube_playlist_handler.py

# Run a single test
pytest tests/test_youtube_playlist_handler.py::TestYouTubePlaylistHandler::test_extract_playlist_id_valid

# Run tests with coverage
pytest --cov=src tests

# Run tests in verbose mode
pytest -v tests
```

## Code Style Guidelines

### General Principles
- **Readability First**: Code should be self-documenting and easy to understand
- **Explicit over Implicit**: Prefer clear, explicit code over clever shortcuts
- **Defensive Programming**: Add appropriate error handling and logging
- **Type Hints**: Use type hints where beneficial (not strictly enforced)
- **Documentation**: Include docstrings for all public functions, classes, and modules

### Imports
```python
# Standard library imports first
import os
import sys
import logging

# Third-party imports second
from tqdm import tqdm
import requests

# Local imports last, with relative imports preferred
from .crawler import WebCrawler
from .file_manager import FileManager

# Fallback to absolute imports for direct execution
try:
    from . import youtube_downloader
except ImportError:
    import youtube_downloader  # type: ignore[import-not-found]
```

### Naming Conventions
- **Functions/Methods**: `snake_case` (e.g., `extract_playlist_id`, `process_url`)
- **Classes**: `PascalCase` (e.g., `YouTubePlaylistHandler`, `ContentExtractor`)
- **Variables**: `snake_case` (e.g., `output_dir`, `max_depth`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_DELAY`)
- **Modules**: `snake_case` (e.g., `youtube_playlist_handler.py`)

### Function and Class Structure
- Include comprehensive docstrings with Args, Returns, and Raises sections
- Use logging extensively with `__name__` for logger names
- Handle errors defensively with try/except blocks

### Error Handling
- Use specific exception types when possible
- Always log errors with context and include tracebacks in debug mode
- Return appropriate defaults (False/None) on failure

### Logging
- Use appropriate log levels: DEBUG, INFO, WARNING, ERROR
- Include relevant context in messages
- Never log sensitive information (API keys, passwords)

### Testing
- Write unit tests for all public functions using unittest
- Use descriptive test names: `test_{function_name}_{scenario}`
- Mock external dependencies and test both success/failure cases

### Configuration
- Use environment variables for secrets (API keys)
- Use `.env` files with python-dotenv for local development

## Development Workflow

1. **Before coding**: Run `mypy` and `ruff check` on affected files
2. **Write tests**: Add tests for new functionality first
3. **Implement**: Follow the established patterns and style
4. **Verify**: Run tests and linting before committing
5. **Commit**: Use descriptive commit messages following project conventions

## Common Patterns

### URL Processing
- Validate URLs before processing
- Handle both HTTP and HTTPS
- Extract domain information safely
- Respect robots.txt and rate limits

### File Management
- Use the `FileManager` class for all file operations
- Create directories as needed
- Use safe file naming (sanitize special characters)
- Handle encoding properly (UTF-8)

### YouTube Integration
- Use the YouTube Data API responsibly
- Handle quota limits gracefully
- Cache API responses where appropriate
- Validate API keys securely

Remember: This codebase values reliability, maintainability, and user experience. Always consider edge cases, error conditions, and backwards compatibility when making changes.</content>
<parameter name="filePath">/home/codyt/Documents/Projects/web-downloader/AGENTS.md