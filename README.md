# Website Text-to-Markdown Extractor

A powerful tool that extracts content from websites using [defuddle](https://github.com/kepano/defuddle), an intelligent HTML content extractor. Outputs clean, structured content in multiple formats.

## Features

- **Intelligent Content Extraction**: Uses defuddle to automatically detect and extract main content
- **Multiple Output Formats**: 
  - Markdown (default) - with YAML frontmatter
  - HTML - cleaned and standardized
  - JSON - with full metadata
- **Flexible Content Sources**: 
  - Sitemap-based crawling
  - Recursive page crawling
  - Direct URL extraction
- **Full Defuddle API Support**:
  - All pipeline toggles for fine-tuned extraction
  - Content selector override
  - Debug mode with detailed extraction info
  - Complete metadata extraction
- **Smart Organization**: Automatically organizes output in domain-based directory structure
- **Respectful Crawling**: Respects robots.txt rules and implements rate limiting
- **Direct CLI Access**: Use defuddle CLI directly from the nix package

## Installation

### Using Nix

The recommended way to install is using Nix:

Run once without installing:
```bash
nix run github:Cody-W-Tucker/web-downloader -- https://example.com
```

#### NixOS Installation

For NixOS users, add the package to your system:

```nix
# In your configuration.nix
{ pkgs, ... }:

{
  # Option 1: Using flakes
  inputs.web-downloader.url = "github:Cody-W-Tucker/web-downloader";
  
  environment.systemPackages = with pkgs; [
    # Add other packages here
    inputs.web-downloader.packages.${system}.default
  ];
}
```

See [NIXOS.md](NIXOS.md) for more detailed installation instructions.

### Manual Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd web-downloader

# Install npm dependencies (defuddle, jsdom)
npm ci

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Using Nix
web-downloader https://example.com [OPTIONS]

# Manual installation
python -m src.main https://example.com [OPTIONS]
```

The tool will automatically:
1. Extract the domain name from the URL (e.g., "example.com")
2. Create a directory with that name in your current location
3. Save all downloaded content in that directory structure

### Options

**Basic Options:**
- `--output` - Custom directory to save files (alias: `--output-dir`)
- `--depth` - Maximum crawl depth (default: 5)
- `--delay` - Delay between requests in seconds (default: 1.0)
- `--max-delay` - Maximum delay for exponential backoff (default: 3.0)
- `--ignore-robots` - Ignore robots.txt restrictions
- `--user-agent` - Custom user agent string
- `--sitemap-only` - Only use sitemap, don't crawl recursively if sitemap fails
- `-v`, `--verbose` - Increase verbosity:
  - No flag: Only errors and final summary
  - `-v`: Informational messages
  - `-vv`: Debug messages

**Output Format Options:**
- `--format` - Output format: `markdown` (default), `html`, or `json`
  - `markdown`: Clean markdown with YAML frontmatter metadata
  - `html`: Raw Defuddle HTML output
  - `json`: Raw Defuddle JSON per page, plus a combined `site.json`

**Content Extraction Options:**
- `--content-selector` - CSS selector to use as main content element (bypasses auto-detection)
- `--no-remove-hidden` - Keep elements hidden via CSS (useful for CSS sidenote layouts)
- `--no-remove-low-scoring` - Don't remove low-scoring content blocks
- `--no-standardize` - Don't standardize HTML elements (headings, code blocks, footnotes)
- `--remove-images` - Remove images from the output

### Examples

**Extract as Markdown (default):**
```bash
web-downloader https://example.com
```

**Extract as JSON with metadata:**
```bash
web-downloader https://example.com --format json
```

**Extract as clean HTML:**
```bash
web-downloader https://example.com --format html
```

**Extract specific content using CSS selector:**
```bash
web-downloader https://example.com --content-selector "article.post-content"
```

**Enable debug mode for troubleshooting:**
```bash
web-downloader https://example.com -vv --format json
```

**Custom output directory with specific crawl settings:**
```bash
web-downloader https://example.com --output ./my-site --depth 3 --delay 2.0
```

## Direct Defuddle CLI Access

When using the Nix package or `nix develop`, you also get direct access to the defuddle CLI:

```bash
# Parse a URL directly
defuddle parse https://example.com/article

# Output as markdown
defuddle parse https://example.com/article --markdown

# Output as JSON with all metadata
defuddle parse https://example.com/article --json

# Extract just the title
defuddle parse https://example.com/article --property title

# Save to file
defuddle parse https://example.com/article --output result.md

# Enable debug mode
defuddle parse https://example.com/article --debug
```

### Defuddle CLI Options

| Option | Description |
|--------|-------------|
| `--output <file>` / `-o` | Write output to a file |
| `--markdown` / `-m` / `--md` | Convert content to markdown |
| `--json` / `-j` | Output as JSON with metadata |
| `--property <name>` / `-p` | Extract specific property (title, author, etc.) |
| `--debug` | Enable debug mode with verbose logging |

## Output Formats

### Markdown Format (Default)

Extracted content is saved as Markdown with YAML frontmatter:

```markdown
---
title: Article Title
description: Article description
author: John Doe
published: 2024-01-15
domain: example.com
language: en
---

# Article Title

Article content in clean Markdown format...
```

### HTML Format

Raw Defuddle HTML output:

```html
<main>
  <h1>Article Title</h1>
  <p>Clean, standardized HTML content...</p>
</main>
```

### JSON Format

Per-page output matches Defuddle JSON, and the run also writes a combined `site.json`:

```json
{
  "content": "<main>...</main>",
  "title": "Article Title",
  "description": "Article description",
  "domain": "example.com",
  "favicon": "https://example.com/favicon.ico",
  "image": "https://example.com/article-image.jpg",
  "metaTags": [],
  "parseTime": 45,
  "published": "2024-01-15",
  "author": "John Doe",
  "site": "Example Site",
  "schemaOrgData": [],
  "wordCount": 1200
}
```

## Metadata Fields

The following metadata is extracted when available:

| Field | Description |
|-------|-------------|
| `title` | Article title |
| `description` | Article description/summary |
| `author` | Article author |
| `date_published` | Publication date |
| `domain` | Website domain |
| `site` | Website name |
| `language` | Page language (BCP 47 format) |
| `word_count` | Total word count |
| `parse_time` | Extraction time in milliseconds |
| `favicon` | Website favicon URL |
| `image` | Article main image URL |
| `meta_tags` | Raw meta tags object |
| `schema_org_data` | Schema.org structured data |

## Defuddle Features

This tool leverages all defuddle capabilities:

### HTML Standardization

- **Headings**: H1s converted to H2s, duplicate titles removed
- **Code Blocks**: Standardized format with language preservation
- **Footnotes**: Consistent inline reference format
- **Math**: MathJax/KaTeX converted to standard MathML

### Pipeline Toggles

Fine-tune content extraction:

- `remove_exact_selectors` - Remove elements matching exact selectors (ads, etc.)
- `remove_partial_selectors` - Remove elements matching partial selectors
- `remove_hidden_elements` - Remove CSS-hidden elements
- `remove_low_scoring` - Remove low-scoring content blocks
- `remove_small_images` - Remove small images (icons, tracking pixels)
- `standardize` - Standardize HTML elements
- `use_async` - Allow async extractors for third-party APIs

## Development

To contribute or modify:

1. Fork the repository
2. Set up development environment:
   ```bash
   nix develop
   ```
   This shell provides `web-downloader` and `defuddle` directly and does not run `npm ci` or rely on a local `node_modules/`.
3. Make your changes
4. Test your changes:
   ```bash
   web-downloader https://example.com -vv
   ```

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built on [defuddle](https://github.com/kepano/defuddle) by kepano
- Inspired by [Obsidian Web Clipper](https://github.com/obsidianmd/obsidian-clipper)
