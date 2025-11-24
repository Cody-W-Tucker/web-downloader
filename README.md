# Website Text-to-Markdown Extractor

A tool that extracts text content from websites and converts it to Markdown format.

## Features

- Extracts content from websites using sitemaps or recursive crawling
- Converts HTML content to Markdown
- Respects robots.txt rules and implements rate limiting
- Preserves metadata (title, description, etc.)
- Automatically organizes output in a domain-based directory structure

## Installation

### Using Nix

The recommended way to install is using Nix:

Run once without installing
```bash
nix run github:Cody-W-Tucker/web-downloader -- https://example.com
```

#### NixOS Installation

For NixOS users, you can add the package to your system:

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

Clone the repository
Create and activate a virtual environment (optional but recommended)
Install dependencies

```bash
git clone <repository-url>
cd web-downloader

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

- `--output-dir` - Custom directory to save markdown files (overrides domain-based directory)
- `--depth` - Maximum crawl depth (default: 5)
- `--delay` - Delay between requests in seconds (default: 1.0)
- `--max-delay` - Maximum delay for exponential backoff (default: 3.0)
- `--ignore-robots` - Ignore robots.txt restrictions
- `--user-agent` - Custom user agent string
- `--sitemap-only` - Only use sitemap, don't crawl recursively if sitemap fails
- `-v`, `--verbose` - Increase verbosity (can be used multiple times):
  - No flag: Only errors and final summary
  - `-v`: Informational messages
  - `-vv`: Debug messages
