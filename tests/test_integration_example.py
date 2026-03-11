import os

import pytest

from crawler import RateLimitedSession
from defuddle_extractor import DefuddleExtractor
from file_manager import FileManager

pytestmark = pytest.mark.integration


def test_example_com_can_be_fetched():
    session = RateLimitedSession(delay=0.5)
    response = session.get("https://example.com")

    assert response is not None
    assert response.status_code == 200
    assert "Example Domain" in response.text


def test_example_com_content_can_be_extracted_and_saved(temp_output_dir):
    session = RateLimitedSession(delay=0.5)
    response = session.get("https://example.com")
    extractor = DefuddleExtractor()
    metadata, content = extractor.extract_content(
        response.text,
        "https://example.com",
        output_format="markdown",
    )

    assert content

    file_manager = FileManager(temp_output_dir)
    output_path = file_manager.save_markdown(
        content,
        "https://example.com",
        title=metadata.get("title") if metadata else None,
    )

    assert output_path is not None
    assert os.path.exists(output_path)
