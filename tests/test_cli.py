import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from ecotrace.cli import main, _cmd_analyze, _cmd_export, _cmd_benchmark

@pytest.fixture
def dummy_script(tmp_path):
    script_file = tmp_path / "dummy.py"
    script_file.write_text("print('dummy')")
    return str(script_file)

@patch("ecotrace.cli.runpy.run_path")
def test_cli_run_success(mock_run_path, dummy_script):
    test_args = ["ecotrace", "run", dummy_script]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as exc:
            main()
    mock_run_path.assert_called_once_with(dummy_script, run_name="__main__")
    assert exc.value.code == 0

def test_cli_run_file_not_found(capsys):
    test_args = ["ecotrace", "run", "non_existent_file.py"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as exc:
            main()
    captured = capsys.readouterr()
    assert "[ERROR] File not found" in captured.out
    assert exc.value.code == 1

def test_cli_analyze_no_file(capsys):
    test_args = ["ecotrace", "analyze", "-f", "missing_log.csv"]
    with patch.object(sys, 'argv', test_args):
        with pytest.raises(SystemExit) as exc:
            main()
    captured = capsys.readouterr()
    assert "[ERROR] Log file not found" in captured.out
    assert exc.value.code == 1

def test_cli_analyze_success(tmp_path, capsys):
    csv_file = tmp_path / "test_log.csv"
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line\n"
        "2026-04-23 12:00,dummy_func,1.0,0.5,TR,10.0,dummy.py,1\n"
    )
    
    class Args:
        file = str(csv_file)
    
    _cmd_analyze(Args())
    captured = capsys.readouterr()
    assert "dummy_func" in captured.out
    assert "0.5" in captured.out

def test_cli_export_invalid_format(capsys):
    class Args:
        format = "xml"
        output = "test.json"
    with pytest.raises(SystemExit) as exc:
        _cmd_export(Args())
    captured = capsys.readouterr()
    assert "[ERROR] Unsupported format: xml" in captured.out
    assert exc.value.code == 1

@patch("ecotrace.core.EcoTrace.export_json")
def test_cli_export_success(mock_export, capsys):
    class Args:
        format = "json"
        output = "test_out.json"
    _cmd_export(Args())
    mock_export.assert_called_once_with("test_out.json")
    captured = capsys.readouterr()
    assert "[EXPORT] JSON report created successfully" in captured.out

def test_cli_benchmark(capsys):
    class Args:
        iterations = 1000  # Small number for fast test
    
    _cmd_benchmark(Args())
    captured = capsys.readouterr()
    assert "EcoTrace - Overhead Benchmark Results" in captured.out
    assert "Baseline (avg)" in captured.out
    assert "EcoTrace (avg)" in captured.out
