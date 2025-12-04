"""Update manager for MeritsCalc."""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Callable

import requests  # type: ignore[import-untyped]
from packaging import version

from meritscalc.version import __version__

GITHUB_REPO = "PINKgeekPDX/SCMeritsCalc"
RELEASE_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class UpdateManager:
    """Handles checking for updates and downloading installers."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.latest_release_info = None
        self._cancel_download = False

    def check_for_updates(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a new version is available.
        Returns: (is_update_available, version_string, release_notes)
        """
        try:
            self.logger.info(f"Checking for updates from {RELEASE_API_URL}")
            response = requests.get(RELEASE_API_URL, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            tag_name = release_data.get("tag_name", "").lstrip("v")

            self.logger.info(
                f"Current version: {__version__}, Latest version: {tag_name}"
            )

            # Validate that tag_name is a valid version string
            try:
                latest_version = version.parse(tag_name)
                current_version = version.parse(__version__)
            except Exception as parse_error:
                self.logger.warning(
                    f"Invalid version tag '{tag_name}': {parse_error}. "
                    f"Skipping version comparison."
                )
                # Return that we're up to date if we can't parse the version
                return False, tag_name, None

            if latest_version > current_version:
                self.latest_release_info = release_data
                return (
                    True,
                    tag_name,
                    release_data.get("body", "No release notes provided."),
                )

            return False, tag_name, None

        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            raise e

    def get_download_url(self) -> str:
        """Get the download URL for the installer asset."""
        if not self.latest_release_info:
            raise ValueError("No update information available.")

        assets = self.latest_release_info.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".exe") and "setup" in name:
                return asset.get("browser_download_url")
            if name.endswith(".exe"):  # Fallback to any exe if setup not found
                return asset.get("browser_download_url")

        raise ValueError("No suitable installer found in the release assets.")

    def download_update(
        self,
        download_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> str:
        """
        Download the update installer.
        download_dir: Optional directory to save the installer.
        progress_callback: function(percentage: float, status: str)
        Returns: path to downloaded file
        """
        self._cancel_download = False
        try:
            url = self.get_download_url()
            self.logger.info(f"Downloading update from {url}")

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            if download_dir:
                download_dir.mkdir(parents=True, exist_ok=True)
                # Try to use a consistent name but safe
                fname = url.split("/")[-1]
                if not fname.endswith(".exe"):
                    fname = "MeritsCalc_Update.exe"
                temp_path = str(download_dir / fname)
            else:
                # Create a temp file
                fd, temp_path = tempfile.mkstemp(
                    suffix=".exe", prefix="MeritsCalc_Setup_"
                )
                os.close(fd)

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancel_download:
                        self.logger.info("Download cancelled by user.")
                        f.close()
                        os.remove(temp_path)
                        raise InterruptedError("Download cancelled")

                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and progress_callback:
                            percent = (downloaded_size / total_size) * 100
                            progress_callback(
                                percent, f"Downloading... {int(percent)}%"
                            )

            self.logger.info(f"Download complete: {temp_path}")
            return temp_path

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise e

    def cancel_download(self):
        """Cancel the current download."""
        self._cancel_download = True

    def run_installer(self, installer_path: str):
        """Run the installer and exit the application."""
        try:
            self.logger.info(f"Starting installer: {installer_path}")
            if sys.platform == "win32":
                # Use Popen to start independent process
                subprocess.Popen([installer_path, "/SILENT"])
            else:
                # Fallback for other platforms (though this app seems win32 focused)
                subprocess.Popen([installer_path])

            # We rely on the caller to quit the app
        except Exception as e:
            self.logger.error(f"Failed to start installer: {e}")
            raise e
