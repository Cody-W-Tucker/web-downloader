import sys
from unittest.mock import MagicMock, patch

import main


def test_default_output_dir_uses_domain_name():
    assert main.default_output_dir_for_url("https://www.example.com/page") == "./example.com"


def test_default_output_dir_falls_back_when_hostname_missing():
    assert main.default_output_dir_for_url("not-a-url") == "./output"


def test_parse_arguments_accepts_output_alias(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-downloader", "https://example.com", "--output", "./site"],
    )

    args = main.parse_arguments()

    assert args.output_dir == "./site"


def test_parse_arguments_accepts_output_dir_alias(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-downloader", "https://example.com", "--output-dir", "./site"],
    )

    args = main.parse_arguments()

    assert args.output_dir == "./site"


def test_parse_arguments_default_output_dir_is_none(monkeypatch):
    """Test that output_dir defaults to None when not provided."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-downloader", "https://example.com"],
    )

    args = main.parse_arguments()

    assert args.output_dir is None


def test_main_uses_default_output_dir_when_not_provided(monkeypatch, capsys):
    """Test that main() works when output_dir is not provided (defaults to domain-based directory).
    
    This test verifies the fix for the bug where os.path.abspath(args.output_dir) was called
    with None when no --output flag was provided, causing a TypeError.
    """
    monkeypatch.setattr(
        sys,
        "argv",
        ["web-downloader", "https://example.com", "--sitemap-only"],
    )
    
    # Mock all the dependencies to avoid actual network calls and file operations
    with patch('main.extract_sitemap_urls_recursive') as mock_sitemap, \
         patch('main.RateLimitedSession') as mock_session, \
         patch('main.DefuddleExtractor') as mock_extractor, \
         patch('main.FileManager') as mock_file_manager, \
         patch('main.setup_logging'), \
         patch('sys.exit') as mock_exit:
        
        # Setup mocks
        mock_sitemap.return_value = ['https://example.com/page1']
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.is_available.return_value = True
        mock_extractor.return_value = mock_extractor_instance
        mock_file_manager_instance = MagicMock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        # Mock process_url to return success without doing actual work
        with patch('main.process_url', return_value=True):
            # This should not raise TypeError about NoneType
            main.main()
        
        # Verify the program didn't exit with error
        # Check that sys.exit was not called with error code 1
        error_exits = [call for call in mock_exit.call_args_list 
                      if call.args and call.args[0] == 1]
        assert len(error_exits) == 0, "main() should not exit with error when output_dir is not provided"
        
        # Verify FileManager was initialized with the default output directory (derived from domain)
        mock_file_manager.assert_called_once()
        call_kwargs = mock_file_manager.call_args[1] if mock_file_manager.call_args[1] else mock_file_manager.call_args[0]
        output_dir_arg = call_kwargs.get('output_dir') if isinstance(call_kwargs, dict) else call_kwargs[0] if call_kwargs else None
        
        # The output directory should be derived from the domain, not None
        assert output_dir_arg == "./example.com", f"Expected './example.com' but got {output_dir_arg}"
