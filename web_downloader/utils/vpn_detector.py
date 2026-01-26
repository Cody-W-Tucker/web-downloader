"""
VPN detection utilities for web-downloader
"""

import subprocess
import shlex
import logging

logger = logging.getLogger(__name__)


class VPNDetector:
    """Detect VPN status, with focus on Mullvad on NixOS"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def run_command(self, cmd):
        """Run shell command and return (success, output, error)"""
        try:
            result = subprocess.run(
                shlex.split(cmd), capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return False, "", str(e)

    def check_mullvad_status(self):
        """
        Check Mullvad VPN status

        Returns:
            tuple: (is_secured: bool, status_message: str)
        """
        # Check daemon first
        daemon_ok, daemon_msg = self._check_mullvad_daemon()
        if not daemon_ok:
            return False, daemon_msg

        # Check connection
        connected, status_msg = self._check_mullvad_connection()
        return connected, status_msg

    def _check_mullvad_daemon(self):
        """Check if mullvad-daemon service is running"""
        success, output, error = self.run_command("systemctl is-active mullvad-daemon")
        if success and output == "active":
            return True, "Mullvad daemon is running"
        elif output == "inactive":
            return False, "Mullvad daemon is not running"
        else:
            return False, "Failed to check daemon status: " + error

    def _check_mullvad_connection(self):
        """Check Mullvad VPN connection status"""
        success, output, error = self.run_command("mullvad status")
        if success:
            if "Connected" in output:
                return True, "Connected: " + output
            else:
                return False, "Disconnected: " + output
        else:
            return False, "Failed to get status: " + error

    def prompt_user_if_needed(self, secured, status_msg):
        """
        Prompt user if VPN is not secured

        Returns:
            bool: True if user wants to proceed, False to abort
        """
        if secured:
            self.logger.info("VPN check passed: " + status_msg)
            return True

        print("\nWARNING: " + status_msg)
        print("YouTube transcript downloads may be blocked without VPN.")
        print()

        while True:
            try:
                choice = input("Proceed anyway? (y/n): ").strip().lower()
                if choice in ["y", "yes"]:
                    return True
                elif choice in ["n", "no"]:
                    return False
                else:
                    print("Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                return False
