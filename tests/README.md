# Web Downloader Test Suite

This directory contains a comprehensive test suite for the web-downloader project, including unit tests and integration tests that use example.com to verify real-world functionality.

## Test Structure

```
tests/
├── conftest.py                  # Test configuration and fixtures
├── test_crawler.py              # Tests for RateLimitedSession and WebCrawler
├── test_defuddle_extractor.py   # Tests for DefuddleExtractor
├── test_file_manager.py         # Tests for FileManager
├── test_integration_example.py # Integration tests using example.com
├── test_robots_parser.py        # Tests for RobotsHandler
└── test_sitemap_parser.py       # Tests for sitemap parser
```

## Running Tests

### Run All Tests

```bash
nix develop -c pytest tests/
```

### Run Unit Tests Only (No Network)

```bash
nix develop -c pytest tests/ -m "not integration"
```

### Run Integration Tests Only (Requires Network)

```bash
nix develop -c pytest tests/test_integration_example.py -v
```

### Run Specific Test File

```bash
nix develop -c pytest tests/test_crawler.py -v
```

### Run with Coverage

```bash
nix develop -c pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests (Fast, Isolated)

- **test_crawler.py**: Tests for URL normalization, link extraction, session management
- **test_defuddle_extractor.py**: Tests for HTML content extraction with defuddle
- **test_file_manager.py**: Tests for file path generation, frontmatter, saving
- **test_robots_parser.py**: Tests for robots.txt parsing and permission checking
- **test_sitemap_parser.py**: Tests for sitemap XML parsing

### Integration Tests (Uses example.com)

- **test_integration_example.py**: Full end-to-end tests making real HTTP requests
  - Tests against example.com to verify actual functionality
  - Tests all output formats (markdown, html, json)
  - Tests rate limiting with real requests
  - Tests robots.txt handling with real servers
  - Tests complete extraction workflow

## Key Features Tested

### RateLimitedSession
- Rate limiting between requests
- User agent configuration
- Domain-based request tracking
- Robots.txt respect

### WebCrawler
- Link extraction from HTML
- URL normalization
- Internal vs external URL detection
- Crawl depth limiting

### DefuddleExtractor
- Content extraction from HTML
- Metadata extraction (title, author, etc.)
- Multiple output formats (markdown, html, json)
- Pipeline options (image removal, standardization)

### FileManager
- URL to filepath conversion
- Filename sanitization
- YAML frontmatter handling
- Naming conflict resolution
- Directory structure creation

### RobotsHandler
- Robots.txt fetching and parsing
- Crawl delay extraction
- Permission checking (can_fetch)
- Sitemap extraction
- 403 error handling

### SitemapParser
- Sitemap URL generation
- XML sitemap parsing
- Sitemap index handling
- Recursive sitemap processing

## Fixtures (conftest.py)

The test suite includes several helpful fixtures:

- `temp_output_dir`: Creates a temporary directory for test outputs
- `sample_html`: Sample HTML content for testing
- `sample_sitemap_xml`: Sample sitemap XML
- `sample_sitemap_index_xml`: Sample sitemap index XML
- `sample_robots_txt`: Sample robots.txt content
- `mock_response`: Factory for creating mock response objects

## Test Markers

- `integration`: Tests that make real HTTP requests (slower, requires network)
- `slow`: Tests that may take longer to run
- `unit`: Fast, isolated unit tests

## Example Test Output

```
$ nix develop -c pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.13.3, pytest-8.3.5
rootdir: /home/codyt/Projects/web-downloader
configfile: pytest.ini
collected 111 items

tests/test_crawler.py::TestNormalizeUrl::test_normalize_absolute_url PASSED
tests/test_crawler.py::TestNormalizeUrl::test_normalize_relative_url PASSED
...
tests/test_integration_example.py::TestEndToEndWorkflow::test_complete_extraction_workflow PASSED
============================= 111 passed in 15.37s ===========================
```

## Continuous Integration

These tests can be run in CI/CD pipelines:

```bash
# Run unit tests only (fast)
nix develop -c pytest tests/ -m "not integration" --tb=short

# Run all tests including integration (requires network)
nix develop -c pytest tests/ --tb=short
```

## Adding New Tests

When adding new tests:

1. Use descriptive test names that explain what is being tested
2. Group related tests in classes
3. Use fixtures from conftest.py for common setup
4. Mark slow or network-dependent tests with appropriate markers
5. Follow the existing test structure and naming conventions

Example:

```python
def test_new_feature_handles_edge_case(self, temp_output_dir):
    """Test that the new feature handles edge cases correctly."""
    # Setup
    fm = FileManager(temp_output_dir)
    
    # Execute
    result = fm.some_method()
    
    # Assert
    assert result is not None
```

## Troubleshooting

### Tests Fail Due to Network Issues

If integration tests fail due to network connectivity:

```bash
# Run only unit tests
nix develop -c pytest tests/ -m "not integration"
```

### Import Errors

If you see import errors, ensure you're running tests from the nix develop shell:

```bash
nix develop -c pytest tests/
```

### Rate Limiting Test Failures

Integration tests include delays between requests to avoid overwhelming example.com. If tests timeout, you may need to increase the timeout:

```bash
nix develop -c pytest tests/test_integration_example.py --timeout=120
```
