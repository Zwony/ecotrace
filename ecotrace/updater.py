"""EcoTrace Auto-Update Module — PyPI version checker and interactive upgrader.

This module provides a non-blocking, fail-safe mechanism to check for newer
versions of EcoTrace on PyPI and optionally upgrade the package via pip.

The update check is designed to NEVER interfere with the main application:
    - All network errors are silently caught.
    - Timeouts are capped at 3 seconds.
    - CI/CD environments can disable the check entirely via ``check_updates=False``.

Typical usage::

    from ecotrace.updater import check_for_updates
    check_for_updates()  # Runs once during EcoTrace.__init__
"""

import subprocess
import sys

# --- Constants ---------------------------------------------------------------
PYPI_PACKAGE_NAME = "ecotrace"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
PYPI_REQUEST_TIMEOUT_S = 3  # Maximum wait time for PyPI response


def _fetch_latest_version():
    """Queries the PyPI JSON API for the latest published version of EcoTrace.

    Uses the public PyPI JSON endpoint which requires no authentication.
    The request is capped at PYPI_REQUEST_TIMEOUT_S seconds to prevent
    blocking the main application on slow or unavailable networks.

    Returns:
        str or None: The latest version string (e.g. '6.1.0') if the
        query succeeds, or None if any error occurs (network failure,
        timeout, malformed response, etc.).
    """
    try:
        import requests
        response = requests.get(PYPI_JSON_URL, timeout=PYPI_REQUEST_TIMEOUT_S)
        response.raise_for_status()

        data = response.json()
        return data.get("info", {}).get("version")
    except Exception as e:
        # Fail silently, but log exactly what went wrong for debugging
        from .logger import logger
        logger.debug(f"PyPI version fetch failed: {e}")
        return None

def _is_newer_version(current, latest):
    """Compares two semantic version strings to determine if an update exists.

    Uses ``packaging.version.parse`` for robust PEP 440-compliant comparison,
    handling edge cases like pre-release tags and epoch versions correctly.

    Args:
        current: The currently installed version string (e.g. '6.0.0').
        latest: The latest available version string from PyPI (e.g. '6.1.0').

    Returns:
        bool: True if ``latest`` is strictly newer than ``current``,
        False otherwise or if parsing fails.
    """
    try:
        from packaging.version import parse
        return parse(latest) > parse(current)
    except Exception as e:
        # If packaging is unavailable, fall back to simple string comparison
        from .logger import logger
        logger.debug(f"Semantic version comparison fallback due to: {e}")
        return latest != current


def _run_pip_upgrade():
    """Executes ``pip install --upgrade ecotrace`` as a subprocess.

    Uses ``sys.executable`` to ensure the correct Python interpreter is used,
    which is critical in virtual environments and conda setups.

    Returns:
        bool: True if the upgrade command completed successfully (exit code 0),
        False if the command failed or raised an exception.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", PYPI_PACKAGE_NAME],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for slow networks
        )
        return result.returncode == 0
    except Exception as e:
        from .logger import logger
        logger.debug(f"Subprocess pip upgrade failed: {e}")
        return False


def check_for_updates(current_version):
    """Main entry point: checks PyPI for updates and prompts the user interactively.

    This function is called once during ``EcoTrace.__init__``. It performs
    the following steps:

    1. Queries PyPI for the latest version (with a 3-second timeout).
    2. Compares version strings using semantic versioning.
    3. If a newer version exists, displays a friendly prompt in the terminal.
    4. If the user responds 'y', triggers ``pip install --upgrade ecotrace``.
    5. If any step fails, execution continues silently.

    The entire function is wrapped in a try/except to guarantee that EcoTrace
    initialization is NEVER blocked or crashed by the update mechanism.

    Args:
        current_version: The currently installed version string from
            ``ecotrace.__version__`` (e.g. '6.0.0').

    Returns:
        None: This function operates via side effects (terminal I/O).
    """
    try:
        latest_version = _fetch_latest_version()

        # If we couldn't reach PyPI or parse the response, skip silently
        if latest_version is None:
            return

        # No update needed — current version is up to date
        if not _is_newer_version(current_version, latest_version):
            return

        from .logger import logger

        # Display a friendly, non-intrusive update prompt
        logger.info(f"🌱 A new version is available! (v{current_version} → v{latest_version})")
        try:
            answer = input("[EcoTrace] Would you like to update? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment (e.g. piped stdin) — skip gracefully
            logger.info("Update skipped (non-interactive environment).")
            return

        if answer == "y":
            logger.info("Starting update...")
            if _run_pip_upgrade():
                logger.info(f"✅ EcoTrace v{latest_version} installed successfully!")
                logger.info("Please restart your application to apply the changes.")
            else:
                from .exceptions import EcoTraceUpdateError
                logger.warning("⚠️ Update failed. Please try manually:")
                logger.warning(f"  pip install --upgrade {PYPI_PACKAGE_NAME}")
        else:
            logger.info("Update skipped.")

    except Exception as e:
        # Ultimate safety net — update check must NEVER crash the application
        from .logger import logger
        logger.debug(f"Unexpected error in update checker: {e}")
