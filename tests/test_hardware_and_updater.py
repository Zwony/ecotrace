import io
import plistlib
import subprocess
from unittest.mock import MagicMock, mock_open, patch
import pytest

from ecotrace.hardware import HardwareMonitor
from ecotrace import updater


def test_hardware_check_rapl_linux_success():
    with patch("platform.system", return_value="Linux"):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="12345678")):
                hw = HardwareMonitor()
                assert hw.rapl_available is True


def test_hardware_check_rapl_permission_error():
    with patch("platform.system", return_value="Linux"):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError()):
                hw = HardwareMonitor()
                assert hw.rapl_available is False


def test_hardware_apple_silicon_check_success():
    fake_plist = plistlib.dumps({"CPU Energy (mJ)": 5000})
    fake_proc = MagicMock(returncode=0, stdout=fake_plist)
    with patch("platform.system", return_value="Darwin"):
        with patch("platform.machine", return_value="arm64"):
            with patch("subprocess.run", return_value=fake_proc):
                hw = HardwareMonitor()
                assert hw.apple_silicon_available is True


def test_hardware_apple_silicon_check_failure():
    with patch("platform.system", return_value="Darwin"):
        with patch("platform.machine", return_value="arm64"):
            with patch("subprocess.run", side_effect=subprocess.SubprocessError()):
                hw = HardwareMonitor()
                assert hw.apple_silicon_available is False


def test_hardware_read_powermetrics_energy_success():
    fake_plist = plistlib.dumps({"CPU Energy (mJ)": 2500})
    fake_proc = MagicMock(returncode=0, stdout=fake_plist)
    with patch("platform.system", return_value="Darwin"):
        with patch("platform.machine", return_value="arm64"):
            with patch("subprocess.run", return_value=fake_proc):
                hw = HardwareMonitor()
                energy = hw._read_powermetrics_energy_j()
                assert energy == 2.5


def test_hardware_read_powermetrics_energy_failure():
    fake_proc = MagicMock(returncode=1, stdout=b"")
    with patch("platform.system", return_value="Darwin"):
        with patch("platform.machine", return_value="arm64"):
            with patch("subprocess.run", return_value=fake_proc):
                hw = HardwareMonitor()
                assert hw._read_powermetrics_energy_j() is None


def test_hardware_get_cpu_energy_j_rapl():
    with patch("platform.system", return_value="Linux"):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="5000000")):
                hw = HardwareMonitor()
                hw.rapl_available = True
                assert hw.get_cpu_energy_j() == 5.0


def test_hardware_get_cpu_energy_j_rapl_exception():
    with patch("platform.system", return_value="Linux"):
        with patch("os.path.exists", return_value=True):
            hw = HardwareMonitor()
            hw.rapl_available = True
            with patch("builtins.open", side_effect=IOError("read error")):
                assert hw.get_cpu_energy_j() is None


def test_updater_fetch_latest_version_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"info": {"version": "2.0.0"}}
    with patch("requests.get", return_value=mock_resp):
        assert updater._fetch_latest_version() == "2.0.0"


def test_updater_fetch_latest_version_failure():
    with patch("requests.get", side_effect=Exception("network error")):
        assert updater._fetch_latest_version() is None


def test_updater_is_newer_version():
    assert updater._is_newer_version("1.0.0", "1.1.0") is True
    assert updater._is_newer_version("1.2.0", "1.1.0") is False
    assert updater._is_newer_version("1.0.0", "1.0.0") is False


def test_updater_is_newer_version_fallback():
    with patch("packaging.version.parse", side_effect=ImportError("no packaging")):
        assert updater._is_newer_version("1.0.0", "1.1.0") is True


def test_updater_run_pip_upgrade_success():
    fake_proc = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=fake_proc):
        assert updater._run_pip_upgrade() is True


def test_updater_run_pip_upgrade_failure():
    with patch("subprocess.run", side_effect=Exception("pip error")):
        assert updater._run_pip_upgrade() is False


def test_updater_check_for_updates_flow():
    with patch("ecotrace.updater._fetch_latest_version", return_value="2.0.0"):
        with patch("builtins.input", return_value="y"):
            with patch("ecotrace.updater._run_pip_upgrade", return_value=True):
                updater.check_for_updates("1.0.0")

        with patch("builtins.input", return_value="n"):
            updater.check_for_updates("1.0.0")

        with patch("builtins.input", side_effect=EOFError()):
            updater.check_for_updates("1.0.0")


def test_updater_check_for_updates_noop():
    with patch("ecotrace.updater._fetch_latest_version", return_value="1.0.0"):
        updater.check_for_updates("1.0.0")

    with patch("ecotrace.updater._fetch_latest_version", return_value=None):
        updater.check_for_updates("1.0.0")
