---
title: YouTube Transcript Downloader
dateCreated: 2025-07-10
dateModified: 2026-01-24
---

# YouTube Transcript Downloader

A tool that extracts transcripts from YouTube videos, playlists, and channels, and saves them as Markdown files.

## Features

- Extract transcripts from individual YouTube videos
- Process entire YouTube playlists
- Process all videos from a YouTube channel
- Multi-language support with preference ordering
- Translation options for transcripts
- Clean Markdown formatting with timestamps
- Comprehensive metadata inclusion
- Progress tracking for batch operations

## Installation

1. Clone the repository:

	 ```bash
   git clone https://github.com/yourusername/web-downloader.git
   cd web-downloader
   ```

2. Install dependencies:

	 ```bash
   pip install -r requirements.txt
   ```

3. Set up YouTube API key:
	 - Create a project in the [Google Developers Console](https://console.developers.google.com/)
	 - Enable the YouTube Data API v3
	 - Create an API key
	 - Copy `.env.example` to `.env` and add your API key:

		 ```

		 YOUTUBE_API_KEY=your_api_key_here

		 ```

## Usage

### Command Line

#### Extract Transcripts from a YouTube Playlist

```bash
python -m src --youtube "https://www.youtube.com/playlist?list=PLAYLIST_ID" --output-dir "transcripts/playlist_name"
```

#### Extract Transcripts from a YouTube Channel

```bash
python -m src --youtube-channel "https://www.youtube.com/c/CHANNEL_NAME" --output-dir "transcripts/channel_name"
```

#### Extract with Language Preferences

```bash
python -m src --youtube "https://www.youtube.com/playlist?list=PLAYLIST_ID" --language "en,es,fr" --translate-to "en"
```

### Parameters

- `--youtube`: URL of the YouTube playlist to process
- `--youtube-channel`: URL of the YouTube channel to process
- `--output-dir`: Directory to save the transcripts (default: "output")
- `--language`: Comma-separated list of language codes in order of preference (default: "en")
- `--translate-to`: Language code to translate the transcript to
- `--youtube-api-key`: YouTube Data API key (can also be set in `.env` file)
- `--verbose` or `-v`: Increase verbosity level

## Output Format

Transcripts are saved as Markdown files with the following structure:

```markdown
---
title: "Video Title"
source_url: "https://www.youtube.com/watch?v=VIDEO_ID"
channel: "Channel Name"
channel_url: "https://www.youtube.com/channel/CHANNEL_ID"
published_at: "YYYY-MM-DDTHH:MM:SSZ"
date_extracted: "YYYY-MM-DDTHH:MM:SS.SSSSSS"
type: "youtube_transcript"
---

> Video description...

# Video Title

- **Video URL**: https://www.youtube.com/watch?v=VIDEO_ID
- **Channel**: Channel Name
- **Published**: YYYY-MM-DD
- **Views**: 123456

## Transcript

[00:00:00] This is the transcript text...

[00:00:30] More transcript text...
```

## Directory Structure

Transcripts are organized by channel name:

```
output_directory/
└── Channel Name/
    ├── Video Title 1-VIDEO_ID1.md
    ├── Video Title 2-VIDEO_ID2.md
    └── ...
```

## Limitations

- Requires a YouTube Data API key with sufficient quota
- Only processes videos with available captions
- Maximum of 50 videos per API request (pagination handles more)
- YouTube API daily quota limitations apply

## License

This project is licensed under the MIT License - see the LICENSE file for details.
