"""
Test VPN detector integration
"""

import unittest
from unittest.mock import patch, MagicMock
from web_downloader.utils.vpn_detector import VPNDetector


class TestVPNDetector(unittest.TestCase):
    """Test VPN detector functionality"""

    def setUp(self):
        self.detector = VPNDetector()

    @patch("subprocess.run")
    def test_check_mullvad_status_connected(self, mock_run):
        """Test Mullvad status when connected"""
        # Mock daemon active
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="active", stderr=""),
            MagicMock(returncode=0, stdout="Connected to relay", stderr=""),
        ]

        secured, msg = self.detector.check_mullvad_status()
        self.assertTrue(secured)
        self.assertIn("Connected", msg)

    @patch("subprocess.run")
    def test_check_mullvad_status_disconnected(self, mock_run):
        """Test Mullvad status when disconnected"""
        # Mock daemon active but disconnected
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="active", stderr=""),
            MagicMock(returncode=0, stdout="Disconnected", stderr=""),
        ]

        secured, msg = self.detector.check_mullvad_status()
        self.assertFalse(secured)
        self.assertIn("Disconnected", msg)

    @patch("subprocess.run")
    def test_check_mullvad_daemon_inactive(self, mock_run):
        """Test Mullvad daemon inactive"""
        mock_run.return_value = MagicMock(returncode=0, stdout="inactive", stderr="")

        secured, msg = self.detector.check_mullvad_status()
        self.assertFalse(secured)
        self.assertIn("not running", msg)

    @patch("builtins.input")
    def test_prompt_user_proceed(self, mock_input):
        """Test user prompt when choosing to proceed"""
        mock_input.return_value = "y"

        result = self.detector.prompt_user_if_needed(False, "VPN disconnected")
        self.assertTrue(result)

    @patch("builtins.input")
    def test_prompt_user_abort(self, mock_input):
        """Test user prompt when choosing to abort"""
        mock_input.return_value = "n"

        result = self.detector.prompt_user_if_needed(False, "VPN disconnected")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
