import json
from types import SimpleNamespace

import defuddle_extractor as module


def build_extractor(monkeypatch, *, debug=False):
    monkeypatch.setattr(module.DefuddleExtractor, "_find_node", lambda self: "/usr/bin/node")
    monkeypatch.setattr(module.DefuddleExtractor, "_find_wrapper", lambda self: "/tmp/defuddle_wrapper.js")
    return module.DefuddleExtractor(debug=debug)


def test_extract_content_skips_empty_html(monkeypatch):
    extractor = build_extractor(monkeypatch)

    metadata, content = extractor.extract_content("   ", "https://example.com")

    assert metadata is None
    assert content is None


def test_extract_content_builds_expected_wrapper_command(monkeypatch):
    extractor = build_extractor(monkeypatch, debug=True)
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["input"] = kwargs["input"]
        return SimpleNamespace(returncode=0, stdout="Test Page\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    metadata, content = extractor.extract_content(
        "<html><body>test</body></html>",
        "https://example.com/article",
        output_format="json",
        property_name="title",
        content_selector="article",
        pipeline_options={
            "remove_exact_selectors": False,
            "remove_images": True,
            "standardize": False,
            "use_async": False,
        },
    )

    assert metadata is None
    assert content == "Test Page"
    assert calls["input"] == "<html><body>test</body></html>"
    assert calls["cmd"] == [
        "/usr/bin/node",
        "/tmp/defuddle_wrapper.js",
        "--url",
        "https://example.com/article",
        "--format",
        "json",
        "--debug",
        "--property",
        "title",
        "--content-selector",
        "article",
        "--no-remove-exact",
        "--remove-images",
        "--no-standardize",
        "--no-async",
    ]


def test_extract_content_parses_json_output(monkeypatch):
    extractor = build_extractor(monkeypatch)
    payload = {
        "success": True,
        "content": "Rendered article",
        "title": "Article title",
        "description": "Article description",
        "url": "https://example.com/article",
        "wordCount": 42,
    }

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    metadata, content = extractor.extract_content(
        "<html><body>test</body></html>",
        "https://example.com/article",
        output_format="json",
    )

    assert content == "Rendered article"
    assert metadata == {
        "success": True,
        "title": "Article title",
        "description": "Article description",
        "url": "https://example.com/article",
        "wordCount": 42,
    }


def test_extract_content_falls_back_to_raw_output_for_markdown(monkeypatch):
    extractor = build_extractor(monkeypatch)

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="# Test Page\n\nReadable body",
            stderr="",
        ),
    )

    metadata, content = extractor.extract_content(
        "<html><body>test</body></html>",
        "https://example.com/article",
        output_format="markdown",
    )

    assert metadata == {"url": "https://example.com/article"}
    assert content == "# Test Page\n\nReadable body"


def test_extract_content_returns_none_on_wrapper_failure(monkeypatch):
    extractor = build_extractor(monkeypatch)

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="", stderr="boom"),
    )

    metadata, content = extractor.extract_content(
        "<html><body>test</body></html>",
        "https://example.com/article",
    )

    assert metadata is None
    assert content is None


def test_extract_metadata_uses_json_mode(monkeypatch):
    extractor = build_extractor(monkeypatch)
    calls = []

    def fake_extract_content(html_content, url, output_format="markdown", **kwargs):
        calls.append((html_content, url, output_format, kwargs))
        return {"title": "Article title"}, "ignored"

    monkeypatch.setattr(extractor, "extract_content", fake_extract_content)

    metadata = extractor.extract_metadata("<html></html>", "https://example.com/article")

    assert metadata == {"title": "Article title"}
    assert calls == [
        ("<html></html>", "https://example.com/article", "json", {})
    ]
