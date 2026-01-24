# YouTube Transcript Tool - Product Requirements Document (PRD)

## Overview

The web-downloader project currently provides functionality to crawl websites, extract content, and convert it to Markdown format. This PRD outlines the requirements for extending the project to add YouTube transcript extraction capabilities, allowing users to extract transcripts from YouTube videos, playlists, and channels, and save them as well-formatted Markdown files.

## Current State

### Existing Functionality
- **Web Crawling**: The tool can crawl websites, extract content, and convert HTML to Markdown
- **CLI Interface**: Command-line interface with various options for crawling parameters
- **File Management**: Organized output with metadata and proper file naming
- **Rate Limiting & Compliance**: Respects robots.txt and implements rate limiting
- **Technology Stack**: Python-based with dependencies managed via requirements.txt and Nix (flake.nix)

### Codebase Structure
- `src/main.py`: Entry point and orchestrator
- `src/crawler.py`: Handles web requests and rate limiting
- `src/content_extractor.py`: Extracts content from HTML pages
- `src/markdown_converter.py`: Converts HTML to Markdown
- `src/file_manager.py`: Manages file saving operations
- Supporting modules for robots.txt parsing and sitemap handling

## Requirements

### Core Features

#### 1. YouTube Transcript Extraction
- Extract transcripts from individual YouTube videos
- Process entire YouTube playlists (extract all video transcripts)
- Process all videos from a YouTube channel
- Support for multiple languages with preference ordering
- Translation capabilities for transcripts

#### 2. Output Formatting
- Convert transcripts to well-formatted Markdown files
- Include comprehensive metadata (video title, channel, published date, view count, etc.)
- Organize files by channel name in directory structure
- Include timestamps and properly formatted transcript content
- Frontmatter with structured metadata

#### 3. CLI Integration
- Add new command-line arguments for YouTube operations
- Maintain backward compatibility with existing web crawling functionality
- Progress reporting for batch operations
- Error handling and user feedback

### User Experience

#### Command Line Usage Examples
```bash
# Extract transcripts from a YouTube playlist
python -m src --youtube-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --output-dir "transcripts/playlist_name"

# Extract transcripts from a YouTube channel
python -m src --youtube-channel "https://www.youtube.com/c/CHANNEL_NAME" --output-dir "transcripts/channel_name"

# Extract with language preferences
python -m src --youtube-playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --language "en,es,fr" --translate-to "en"
```

#### Output Structure
```
output_directory/
└── Channel Name/
    ├── Video Title 1-VIDEO_ID1.md
    ├── Video Title 2-VIDEO_ID2.md
    └── ...
```

#### Markdown Output Format
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

## Technical Specifications

### Dependencies

#### New Dependencies to Add
- `langchain>=0.0.312`: For YouTube transcript extraction
- `langchain-community>=0.0.9`: LangChain community components
- `youtube-transcript-api>=0.6.1`: YouTube transcript API wrapper
- `pytube>=15.0.0`: YouTube video metadata extraction
- `google-api-python-client>=2.100.0`: YouTube Data API client
- `python-dotenv>=1.0.0`: Environment variable management

#### Updated Files
- `requirements.txt`: Add new Python dependencies
- `flake.nix`: Update Nix package definitions for new dependencies

### New Components

#### 1. YouTube Playlist Handler (`src/youtube_playlist_handler.py`)
- **Purpose**: Handle YouTube API interactions for playlists and channels
- **Key Functions**:
  - Extract playlist/channel IDs from URLs
  - Fetch video metadata from YouTube Data API
  - Handle pagination for large playlists
  - Support different URL formats (direct ID, custom URLs, @handles)

#### 2. Transcript Processor (`src/transcript_processor.py`)
- **Purpose**: Process transcripts using LangChain and format them
- **Key Functions**:
  - Load transcripts using LangChain's YoutubeLoader
  - Format timestamps consistently
  - Handle multiple languages and translation
  - Convert to Markdown with proper organization

### Modified Components

#### 1. Main Controller (`src/main.py`)
- Add YouTube-specific CLI arguments:
  - `--youtube-playlist URL`: YouTube playlist URL
  - `--youtube-channel URL`: YouTube channel URL
  - `--language LANG`: Comma-separated language codes (default: "en")
  - `--translate-to LANG`: Translation target language
  - `--youtube-api-key KEY`: YouTube Data API key
- Add YouTube processing workflow branch
- Integrate progress reporting with tqdm

#### 2. File Manager (`src/file_manager.py`)
- Extend with YouTube-specific file handling
- Create channel-based directory structure
- Add YouTube metadata to frontmatter
- Handle filename sanitization for videos

### Configuration

#### Environment Variables
- `YOUTUBE_API_KEY`: Required for YouTube Data API access
- `DEFAULT_LANGUAGE`: Default language preference
- `DEFAULT_OUTPUT_DIR`: Default output directory

#### Configuration File (`.env.example`)
```
# YouTube API key for accessing YouTube Data API
YOUTUBE_API_KEY=your_api_key_here

# Default language for transcripts
DEFAULT_LANGUAGE=en

# Default output directory
DEFAULT_OUTPUT_DIR=transcripts
```

## Implementation Plan

### Phase 1: Setup & Environment (Days 1-2)
1. Update `requirements.txt` and `flake.nix` with new dependencies
2. Create `.env.example` configuration file
3. Set up development environment with all dependencies
4. Create skeleton files for new modules

### Phase 2: Core Functionality (Days 3-5)
1. Implement `YouTubePlaylistHandler` class with API integration
2. Implement `TranscriptProcessor` class with LangChain integration
3. Add YouTube-specific methods to `FileManager`
4. Update `main.py` with CLI arguments and workflow

### Phase 3: Integration & Testing (Days 6-7)
1. Integrate all components into main workflow
2. Add comprehensive error handling
3. Implement progress reporting
4. Create integration tests

### Phase 4: Refinement & Documentation (Days 8-10)
1. Performance optimization and caching
2. Update README with usage instructions
3. Add comprehensive logging and error messages
4. Polish user experience

## Acceptance Criteria

### Functional Requirements
- [ ] Can extract transcripts from individual YouTube videos
- [ ] Can process entire YouTube playlists (all videos)
- [ ] Can process all videos from YouTube channels
- [ ] Supports multiple language preferences
- [ ] Supports transcript translation
- [ ] Produces well-formatted Markdown output
- [ ] Organizes output by channel name
- [ ] Includes comprehensive metadata in output

### Technical Requirements
- [ ] Maintains backward compatibility with existing web crawling
- [ ] Handles missing transcripts gracefully (skip with warning)
- [ ] Implements proper error handling and logging
- [ ] Respects YouTube API quotas and rate limits
- [ ] Supports pagination for large playlists/channels
- [ ] Provides progress feedback for batch operations

### Quality Requirements
- [ ] Comprehensive test coverage for new functionality
- [ ] Clear documentation and usage examples
- [ ] Proper error messages and user feedback
- [ ] Code follows existing project conventions
- [ ] Dependencies properly managed in both pip and Nix environments

### Performance Requirements
- [ ] Efficient processing of large playlists (100+ videos)
- [ ] Reasonable processing time per video
- [ ] Memory efficient for long transcripts
- [ ] Graceful handling of API rate limits

## Testing Strategy

### Unit Tests
- Test YouTube URL parsing and ID extraction
- Test transcript formatting and timestamp handling
- Test file path generation and sanitization
- Test LangChain integration

### Integration Tests
- Test end-to-end playlist processing
- Test channel processing workflow
- Test language selection and translation
- Test output format and directory structure

### Manual Testing
- Verify output quality with real playlists
- Test with various channel types and video formats
- Test error scenarios (missing API key, invalid URLs, etc.)
- Performance testing with large datasets

## Risks and Mitigations

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| YouTube API quota limitations | High - Could block functionality | Implement caching, batch processing, and clear quota warnings |
| Missing transcripts for videos | Medium - Incomplete processing | Skip gracefully with warnings, continue processing other videos |
| Dependency compatibility issues | Medium - Build failures | Pin dependency versions, test thoroughly in development |
| Changes in YouTube API/website | High - Breaking changes | Modular design for easy updates, monitor API changes |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large playlists causing timeouts | Medium - User frustration | Implement pagination, progress reporting, and resumable processing |
| Memory usage with long transcripts | Low - Performance issues | Stream processing, chunk large transcripts |
| API key security | High - Security breach | Never commit keys, use environment variables, document security practices |

## Success Metrics

- Successfully extracts transcripts from 95% of videos with available captions
- Processes playlists/channels with 99% reliability
- Output format meets user requirements for readability and metadata completeness
- CLI interface provides clear feedback and error messages
- No breaking changes to existing web crawling functionality

## Future Enhancements

- Support for concurrent processing of multiple videos
- Integration with Whisper API for videos without captions
- Custom Markdown templates for different output formats
- Video filtering by date, view count, or other criteria
- Support for additional video platforms (Vimeo, Twitch, etc.)

---

*This PRD was created based on the planning documents in `plans/thoughts/` and analysis of the current web-downloader codebase.*