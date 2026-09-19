import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from ecotrace import report
from ecotrace.exceptions import ReportGenerationError


def test_sanitize_for_pdf():
    assert report.sanitize_for_pdf("Hello World") == "Hello World"
    assert report.sanitize_for_pdf("Carbon  Footprint 100%") == "Carbon  Footprint 100%"


def test_create_cpu_usage_chart_empty():
    assert report.create_cpu_usage_chart([]) is None


def test_create_cpu_usage_chart_valid():
    samples = [(0.0, 15.0), (0.5, 30.0), (1.0, 45.0)]
    chart_path = report.create_cpu_usage_chart(samples, core_count=2)
    assert chart_path is not None
    assert os.path.exists(chart_path)
    os.unlink(chart_path)


def test_create_cpu_usage_chart_exception():
    with patch("matplotlib.pyplot.subplots", side_effect=RuntimeError("plot failed")):
        assert report.create_cpu_usage_chart([(0.0, 10.0)]) is None


def test_create_gpu_usage_chart_empty():
    assert report.create_gpu_usage_chart([]) is None


def test_create_gpu_usage_chart_valid():
    samples = [(0.0, 40.0), (0.5, 60.0), (1.0, 50.0)]
    chart_path = report.create_gpu_usage_chart(samples)
    assert chart_path is not None
    assert os.path.exists(chart_path)
    os.unlink(chart_path)


def test_create_gpu_usage_chart_exception():
    with patch("matplotlib.pyplot.subplots", side_effect=RuntimeError("plot failed")):
        assert report.create_gpu_usage_chart([(0.0, 20.0)]) is None


def test_get_gemini_insights_no_key():
    assert report.get_gemini_insights(None, {}, {}, [], "TR") is None


def test_get_gemini_insights_mocked():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Optimize loops to reduce carbon."
    mock_model.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model

    with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
        insights = report.get_gemini_insights(
            api_key="fake-key",
            cpu_info={"brand": "Test CPU", "cores": 4, "tdp": 65.0},
            gpu_info={"brand": "Test GPU", "tdp": 120.0},
            history=[["2026-09-19", "calc", "1.2", "0.005", "TR", "25.0"]],
            region_code="DE",
        )
        assert insights == "Optimize loops to reduce carbon."


def test_get_gemini_insights_exception_handled():
    with patch.dict("sys.modules", {"google.generativeai": None}):
        res = report.get_gemini_insights("fake-key", {}, {}, [], "US")
        assert res is not None
        assert "Gemini Insights unavailable" in res or res is None


def test_generate_pdf_report_minimal(tmp_path):
    pdf_path = str(tmp_path / "test_report.pdf")
    report.generate_pdf_report(
        filename=pdf_path,
        cpu_info={"brand": "Intel Core i7", "cores": 8, "tdp": 65.0},
        gpu_info=None,
        region_code="TR",
        log_file=str(tmp_path / "non_existent.csv"),
    )
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0


def test_generate_pdf_report_full(tmp_path):
    csv_file = tmp_path / "audit.csv"
    csv_file.write_text(
        "timestamp,function_name,duration_seconds,carbon_emitted_g,region,cpu_percent\n"
        "2026-09-19 12:00:00,process_batch,2.5,0.01234567,TR,45.0\n"
        "2026-09-19 12:01:00,train_step,5.0,0.04567890,TR,80.0\n"
    )

    pdf_path = str(tmp_path / "full_report.pdf")
    comparison_data = {
        "func1": {"func_name": "process_batch", "duration": 2.5, "cpu_percent": 45.0, "carbon": 0.0123},
        "func2": {"func_name": "train_step", "duration": 5.0, "cpu_percent": 80.0, "carbon": 0.0456},
    }

    report.generate_pdf_report(
        filename=pdf_path,
        cpu_info={"brand": "AMD Ryzen 9", "cores": 16, "tdp": 105.0},
        gpu_info={"brand": "NVIDIA RTX 4090", "tdp": 450.0},
        region_code="FR",
        comparison=comparison_data,
        cpu_samples=[(0.0, 30.0), (1.0, 50.0), (2.0, 40.0)],
        gpu_samples=[(0.0, 60.0), (1.0, 80.0), (2.0, 70.0)],
        api_key=None,
        log_file=str(csv_file),
    )

    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 1000


def test_generate_pdf_report_failure(tmp_path):
    with patch("fpdf.fpdf.FPDF.output", side_effect=OSError("Disk full")):
        with pytest.raises(ReportGenerationError):
            report.generate_pdf_report(
                filename=str(tmp_path / "fail.pdf"),
                log_file=str(tmp_path / "empty.csv"),
            )
