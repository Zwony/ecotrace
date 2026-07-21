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
    mock_export.assert_called_once()
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


def test_cli_history_missing_file(capsys):
    class Args:
        file = "non_existent_history.csv"
        runs = None
    from ecotrace.cli import _cmd_history
    with pytest.raises(SystemExit) as exc:
        _cmd_history(Args())
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "[ERROR] Log file not found" in captured.out


def test_cli_history_success(tmp_path, capsys):
    csv_file = tmp_path / "history_test_log.csv"
    # Write a test CSV with RunID and RunLabel
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line,RunID,RunLabel\n"
        "2026-06-13 12:00,func_a,1.5,0.25,TR,10.0,dummy.py,1,run123,label123\n"
        "2026-06-13 12:05,func_b,2.0,0.35,TR,12.0,dummy.py,5,run123,label123\n"
        "2026-06-13 12:10,func_c,1.0,0.15,US,15.0,dummy.py,10,,legacy_label\n"
    )
    
    class Args:
        file = str(csv_file)
        runs = None

    from ecotrace.cli import _cmd_history
    _cmd_history(Args())
    captured = capsys.readouterr()
    # Check if run123 and legacy are summarized properly
    assert "run123" in captured.out
    assert "label123" in captured.out
    assert "legacy" in captured.out
    assert "0.6000" in captured.out  # sum of carbon for run123
    assert "0.1500" in captured.out  # carbon for legacy


def test_cli_trends_success(tmp_path, capsys):
    csv_file = tmp_path / "trends_test_log.csv"
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line,RunID,RunLabel\n"
        "2026-06-13 12:00,func_a,1.5,0.25,TR,10.0,dummy.py,1,run123,label123\n"
        "2026-06-13 12:05,func_b,2.0,0.75,TR,12.0,dummy.py,5,run456,label456\n"
    )

    class Args:
        file = str(csv_file)
        runs = 5

    from ecotrace.cli import _cmd_trends
    _cmd_trends(Args())
    captured = capsys.readouterr()
    assert "EcoTrace — Carbon Trends" in captured.out
    assert "run123" in captured.out
    assert "run456" in captured.out




def test_cli_export_csv(tmp_path, capsys):
    csv_file = tmp_path / "export_test_log.csv"
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line,RunID,RunLabel\n"
        "2026-06-13 12:00,func_a,1.5,0.25,TR,10.0,dummy.py,1,run1,label1\n"
        "2026-06-13 12:05,func_b,2.0,0.75,TR,12.0,dummy.py,5,run2,label2\n"
    )
    out_file = tmp_path / "filtered_out.csv"
    
    class Args:
        format = "csv"
        file = str(csv_file)
        output = str(out_file)
        run = "run1"
        func = None
        
    from ecotrace.cli import _cmd_export
    _cmd_export(Args())
    captured = capsys.readouterr()
    assert "Filtered CSV report written" in captured.out
    
    # Read output and verify it is filtered
    content = out_file.read_text()
    assert "func_a" in content
    assert "func_b" not in content

def test_cli_diff_success(tmp_path, capsys):
    csv_file = tmp_path / "diff_test_log.csv"
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line,RunID,RunLabel\n"
        "2026-06-13 12:00,func_a,1.0,0.20,TR,10.0,dummy.py,1,run1,label1\n"
        "2026-06-13 12:05,func_b,2.0,0.30,TR,12.0,dummy.py,5,run2,label2\n"
    )
    
    class Args:
        file = str(csv_file)
        run_ids = ["run1", "run2"]
        latest = False
        
    from ecotrace.cli import _cmd_diff
    _cmd_diff(Args())
    captured = capsys.readouterr()
    assert "EcoTrace — Run Comparison Report" in captured.out
    assert "run1" in captured.out
    assert "run2" in captured.out
    assert "+0.10000000" in captured.out # carbon delta

def test_cli_clean_success(tmp_path, capsys):
    csv_file = tmp_path / "clean_test_log.csv"
    csv_file.write_text(
        "Date,Function,Duration(s),Carbon(gCO2),Region,AvgCPU(%),FilePath,Line,RunID,RunLabel\n"
        "2026-06-11 12:00,func_a,1.0,0.20,TR,10.0,dummy.py,1,run1,label1\n"
        "2026-06-12 12:00,func_b,2.0,0.30,TR,12.0,dummy.py,5,run2,label2\n"
        "2026-06-13 12:00,func_c,3.0,0.40,TR,12.0,dummy.py,10,run3,label3\n"
    )
    
    class Args:
        file = str(csv_file)
        before = "2026-06-12"
        keep_runs = None
        
    from ecotrace.cli import _cmd_clean
    _cmd_clean(Args())
    captured = capsys.readouterr()
    assert "Trimmed 1 entries" in captured.out
    assert os.path.exists(str(csv_file) + ".bak")
    
    # Read output and verify first entry is deleted
    content = csv_file.read_text()
    assert "func_a" not in content
    assert "func_b" in content
    assert "func_c" in content

def test_cli_reset_success(tmp_path, capsys):
    csv_file = tmp_path / "reset_test_log.csv"
    csv_file.write_text("dummy content")
    
    class Args:
        file = str(csv_file)
        yes = True
        
    from ecotrace.cli import _cmd_reset
    _cmd_reset(Args())
    assert not os.path.exists(csv_file)


