import json
import os
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = PROJECT_ROOT / "src" / "defuddle_wrapper.js"


def _node_binary():
    return os.environ.get("NIX_NODE_PATH") or shutil.which("node") or shutil.which("nodejs")


def run_wrapper(tmp_path, *args, html):
    node_binary = _node_binary()
    assert node_binary, "Node.js is required for defuddle wrapper tests"

    env = os.environ.copy()
    env.setdefault("DEFUDDLE_NODE_MODULES", str(PROJECT_ROOT / "node_modules"))

    return subprocess.run(
        [node_binary, str(WRAPPER_PATH), *args],
        input=html,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
        timeout=60,
    )


def test_wrapper_returns_json_payload(tmp_path, sample_html):
    result = run_wrapper(
        tmp_path,
        "--url",
        "https://example.com/article",
        "--format",
        "json",
        html=sample_html,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)

    assert payload["title"] == "Test Page"
    assert "Test Heading" in payload["content"]
    assert "success" not in payload
    assert "url" not in payload


def test_wrapper_returns_html_content_for_html_format(tmp_path, sample_html):
    result = run_wrapper(
        tmp_path,
        "--url",
        "https://example.com/article",
        "--format",
        "html",
        html=sample_html,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("<main>")
    assert "Test Heading" in result.stdout
    assert "Footer content" not in result.stdout


def test_wrapper_returns_single_property(tmp_path, sample_html):
    result = run_wrapper(
        tmp_path,
        "--url",
        "https://example.com/article",
        "--format",
        "json",
        "--property",
        "title",
        html=sample_html,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Test Page"


def test_wrapper_requires_url(tmp_path, sample_html):
    result = run_wrapper(tmp_path, "--format", "json", html=sample_html)

    assert result.returncode == 1
    assert "--url is required" in result.stderr


def test_wrapper_requires_html_input(tmp_path):
    result = run_wrapper(
        tmp_path,
        "--url",
        "https://example.com/article",
        "--format",
        "json",
        html="",
    )

    assert result.returncode == 1
    assert "No HTML content provided" in result.stderr
