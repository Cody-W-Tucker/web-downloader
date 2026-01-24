# Website Text-to-Markdown Extractor & YouTube Transcript Downloader

A tool that extracts text content from websites using sitemaps/recursive crawling **and** downloads YouTube transcripts from videos, playlists, and channels, converting everything to clean Markdown format.

## Features

- Extracts content from websites using sitemaps or recursive crawling
- Converts HTML content to Markdown
- **Downloads YouTube transcripts from individual videos, playlists, and channels**
- **Multi-language support with translation capabilities**
- Respects robots.txt rules and implements rate limiting
- Preserves metadata (title, description, etc.)
- Automatically organizes output in a domain/channel-based directory structure
- Progress tracking with tqdm for batch operations
- Comprehensive error handling and logging

## Installation

### Using Nix (Recommended)

Run once without installing:
```bash
nix run github:Cody-W-Tucker/web-downloader -- https://example.com
```

#### NixOS Installation

See [NIXOS.md](NIXOS.md) for detailed instructions.

### Manual Installation

```bash
git clone https://github.com/Cody-W-Tucker/web-downloader
cd web-downloader

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

pip install -r requirements.txt
```

**For YouTube features:**
1. Get a YouTube Data API v3 key from [Google Developers Console](https://console.developers.google.com/)
   - Create project → Enable YouTube Data API v3 → Credentials → Create API key
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Add your key:
   ```
   YOUTUBE_API_KEY=your_api_key_here
   ```

## Usage

Basic usage (website or YouTube):
```bash
# Nix
web-downloader [URL or YouTube options]

# Manual
python -m src.main [URL or YouTube options]
```

The tool detects input type:
- Website URL → Web crawling mode
- `--youtube-playlist`/`--youtube-channel` → YouTube mode

### Website Examples
```bash
web-downloader https://example.com --depth 3 --output-dir ./example-site
```

### YouTube Examples

#### Playlist
```bash
web-downloader --youtube-playlist 'https://www.youtube.com/playlist?list=PLexample' --output-dir transcripts/playlist
```

#### Channel
```bash
web-downloader --youtube-channel 'https://www.youtube.com/@channelhandle' --language 'en,es'
```

#### With Translation
```bash
web-downloader --youtube-playlist 'https://www.youtube.com/playlist?list=PLexample' --language 'es,fr' --translate-to 'en'
```

## CLI Options

**Common:**
- `--output-dir DIR` - Output directory
- `-v`, `--verbose` - Verbosity level

**Website-specific:**
- `--depth N` - Max crawl depth (default: 5)
- `--delay S` - Delay between requests (default: 1.0)
- `--max-delay S` - Max backoff delay (default: 3.0)
- `--ignore-robots` - Ignore robots.txt
- `--user-agent UA` - Custom User-Agent
- `--sitemap-only` - Sitemap only

**YouTube-specific:**
- `--youtube-playlist URL` - YouTube playlist URL
- `--youtube-channel URL` - YouTube channel URL
- `--language LANGS` - Comma-separated languages (default: 'en')
- `--translate-to LANG` - Translate to this language
- `--youtube-api-key KEY` - API key (or use .env)

Run `web-downloader --help` for full list.

## Output Structure

### Websites
Domain-based directories with page Markdown files.

### YouTube Transcripts
Organized by channel:
```
output/
└── Channel Name/
    ├── Video Title-VIDEO_ID.md
    └── ...
```

**Markdown Format:**
```markdown
---
title: "Video Title"
source_url: "https://youtube.com/watch?v=VIDEO_ID"
channel: "Channel Name"
channel_url: "..."
published_at: "2026-01-24T12:00:00Z"
date_extracted: "2026-01-24T12:30:00.123456"
type: "youtube_transcript"
---
> Video description...

# Video Title

- **Duration**: 10:30
- **Views**: 1,234
- **Likes**: 56

## Transcript

[00:00:00] Speaker: First words...
[00:00:15] More text...
```

## Troubleshooting

- **No transcripts**: Video has no captions available (auto-generated or manual).
- **API quota exceeded**: Check Google Console; request quota increase or wait 24h.
- **Invalid API key**: Verify key has YouTube Data API v3 enabled.
- **Rate limited**: Retries with backoff automatic; increase `--delay` if needed.
- **Invalid URL**: Supports playlist/channel/@handle formats.

See logs with `-vv` for details.

## Development

Enter dev shell: `nix develop` or `source .venv/bin/activate`

Run tests: `pytest tests`

## License

MIT