import os
import pytest
from pathlib import Path
from src.file_manager import FileManager

def test_sanitize_filename_unicode(tmp_path):
    fm = FileManager(str(tmp_path))
    # Test unicode preservation
    name = "Café Vidéo 🎉 - Test"
    sanitized = fm._sanitize_filename(name)
    assert "Café" in sanitized
    assert "Vidéo" in sanitized
    assert "🎉" in sanitized

def test_save_youtube_transcript(tmp_path):
    fm = FileManager(str(tmp_path))
    video_info = {
        "channel_title": "Test Channel 🎉",
        "title": "Test Video with cafés",
        "video_id": "abc123def",
    }
    markdown_content = """---
title: Test Video with cafés
video_id: abc123def
channel_title: Test Channel 🎉
youtube_url: https://www.youtube.com/watch?v=abc123def
source: YouTube Transcript (via LangChain YoutubeLoader)
date_extracted: 2026-01-24T12:00:00
---
# Transcript
Test content.
"""
    filepath = fm.save_youtube_transcript(video_info, markdown_content)
    assert filepath is not None
    assert os.path.exists(filepath)
    channel_dir = tmp_path / fm._sanitize_filename("Test Channel 🎉")
    assert channel_dir.exists()
    expected_filename = f"{fm._sanitize_filename('Test Video with cafés')}-abc123def.md"
    expected_path = channel_dir / expected_filename
    assert Path(filepath) == expected_path
    with open(filepath, "r", encoding="utf-8") as f:
        saved_content = f.read()
    assert "Test Video with cafés" in saved_content
    assert "🎉" in saved_content

def test_save_youtube_conflict_overwrite(tmp_path):
    fm = FileManager(str(tmp_path))
    video_info = {"channel_title": "Channel", "title": "Video", "video_id": "id1"}
    content1 = "---\ntitle: Video\nvideo_id: id1\nyoutube_url: https://www.youtube.com/watch?v=id1\n---\ncontent1"
    content2 = "---\ntitle: Video\nvideo_id: id1\nyoutube_url: https://www.youtube.com/watch?v=id1\n---\ncontent2"
    fp1 = fm.save_youtube_transcript(video_info, content1)
    fp2 = fm.save_youtube_transcript(video_info, content2)
    assert fp1 == fp2  # same file, overwrite
    with open(fp2, "r") as f:
        saved = f.read()
    assert "content2" in saved  # updated