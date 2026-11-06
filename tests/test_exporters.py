import subprocess
import sys
from html.parser import HTMLParser
import pytest
from unittest.mock import MagicMock, patch
from ecotrace.core import EcoTrace
from ecotrace.exporters.otel import OTelExporter
from ecotrace.exporters.summary import to_html, to_markdown

def test_add_exporter_core_api():
    """Verify the core EcoTrace instance accepts and retains exporters."""
    eco = EcoTrace(quiet=True, check_updates=False)
    assert hasattr(eco, "_exporters")
    assert len(eco._exporters) == 0

    mock_exporter = MagicMock()
    eco.add_exporter(mock_exporter)
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is mock_exporter


def test_accumulate_carbon_falls_back_to_sync_export_when_thread_pool_submit_fails():
    """Exporter dispatch should still work if the background pool cannot accept work."""
    eco = EcoTrace(quiet=True, check_updates=False)
    exporter = MagicMock()
    eco.add_exporter(exporter)

    with patch.object(eco._exporter_pool, "submit", side_effect=RuntimeError("pool closed")):
        eco._accumulate_carbon(
            carbon_emitted=0.005,
            func_name="test_function",
            duration=1.2,
        )

    exporter.export.assert_called_once_with(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2,
        region=eco.region_code,
        run_id=eco._run_id,
        run_label=eco._run_label,
    )

@patch('ecotrace.exporters.otel.metrics')
def test_otel_exporter_registration_and_export(mock_metrics):
    """Verify OTelExporter attaches to EcoTrace and exports metrics successfully."""
    # Setup mock meter and counter
    mock_meter = MagicMock()
    mock_counter = MagicMock()
    mock_metrics.get_meter.return_value = mock_meter
    mock_meter.create_counter.return_value = mock_counter

    eco = EcoTrace(quiet=True, check_updates=False)
    
    # Initialize exporter
    exporter = OTelExporter(ecotrace_instance=eco, meter_name="test.meter")
    
    # Assert registration
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is exporter
    mock_metrics.get_meter.assert_called_once_with("test.meter")
    mock_meter.create_counter.assert_called_once()
    
    # Trigger export through core API simulation
    eco.region_code = "US"  # Mock region for test
    eco._accumulate_carbon(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2
    )
    
    # Wait for the background exporter thread to finish
    eco._exporter_pool.shutdown(wait=True)
    
    # Assert export was called
    mock_counter.add.assert_called_once_with(
        0.005, 
        attributes={
            "ecotrace.function": "test_function",
            "ecotrace.region": "US"
        }
    )

def test_otel_exporter_missing_dependency():
    """Verify OTelExporter handles missing opentelemetry gracefully."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    # Force metrics to be None as if ImportError occurred
    with patch('ecotrace.exporters.otel.metrics', None):
        exporter = OTelExporter(ecotrace_instance=eco)
        
        # Should not crash, just returns early with counter as None
        assert exporter._carbon_counter is None
        
        # Calling export should be a safe no-op
        exporter.export(0.5, "test", 1.0, "GLOBAL")

# /* --- Hybrid End of File / Dosya Sonu --- */ #

from ecotrace.exporters.webhook import WebhookExporter

@patch('requests.post')
def test_webhook_exporter_registration_and_export(mock_post):
    """Verify WebhookExporter attaches to EcoTrace and POSTs metrics successfully."""
    mock_post.return_value.status_code = 200

    eco = EcoTrace(quiet=True, check_updates=False)
    eco._run_id = "test_run_id"
    eco._run_label = "test_label"
    
    exporter = WebhookExporter(ecotrace_instance=eco, url="http://example.com/webhook", headers={"X-Test": "Value"})
    
    assert len(eco._exporters) == 1
    assert eco._exporters[0] is exporter
    
    eco.region_code = "US"
    eco._accumulate_carbon(
        carbon_emitted=0.005,
        func_name="test_function",
        duration=1.2
    )
    
    eco._exporter_pool.shutdown(wait=True)
    
    # Assert requests.post was called with the correct args
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://example.com/webhook"
    assert kwargs["headers"] == {"Content-Type": "application/json", "X-Test": "Value"}
    payload = kwargs["json"]
    assert payload["function"] == "test_function"
    assert payload["carbon_gco2"] == 0.005
    assert payload["duration_s"] == 1.2
    assert payload["region"] == "US"
    assert payload["run_id"] == "test_run_id"
    assert payload["run_label"] == "test_label"

def test_webhook_exporter_missing_dependency():
    """Verify WebhookExporter handles missing requests gracefully."""
    eco = EcoTrace(quiet=True, check_updates=False)
    
    with patch('ecotrace.exporters.webhook.requests', None):
        exporter = WebhookExporter(ecotrace_instance=eco, url="http://example.com")
        assert exporter.url is None
        exporter.export(0.5, "test", 1.0, "GLOBAL")


def _post_one_measurement(mock_post, carbon_emitted=0.005, carbon_limit=None, **exporter_kwargs):
    """Send one measurement through a WebhookExporter and return the JSON body it POSTed."""
    mock_post.return_value.status_code = 200

    eco = EcoTrace(quiet=True, check_updates=False, carbon_limit=carbon_limit)
    eco.region_code = "US"
    WebhookExporter(ecotrace_instance=eco, url="http://example.com/webhook", **exporter_kwargs)

    eco._accumulate_carbon(carbon_emitted=carbon_emitted, func_name="test_function", duration=1.2)
    eco._exporter_pool.shutdown(wait=True)

    mock_post.assert_called_once()
    return mock_post.call_args.kwargs["json"]


@patch('requests.post')
def test_webhook_exporter_default_format_keeps_json_payload(mock_post):
    """Without a format, the payload is the same flat dict the exporter sent before the option existed."""
    payload = _post_one_measurement(mock_post)

    assert set(payload) == {"function", "carbon_gco2", "duration_s", "region", "run_id", "run_label"}
    assert payload["function"] == "test_function"
    assert payload["carbon_gco2"] == 0.005
    assert payload["duration_s"] == 1.2
    assert payload["region"] == "US"
    assert "embeds" not in payload
    assert "blocks" not in payload


@patch('requests.post')
def test_webhook_exporter_json_format_matches_default_payload(mock_post):
    """format="json" is accepted and sends the same payload as the default (run_id differs per EcoTrace)."""
    default_payload = _post_one_measurement(mock_post)
    mock_post.reset_mock()
    json_payload = _post_one_measurement(mock_post, format="json")

    default_payload.pop("run_id")
    json_payload.pop("run_id")
    assert json_payload == default_payload


@patch('requests.post')
def test_webhook_exporter_discord_sends_an_embed(mock_post):
    """format="discord" sends one embed with the function name, gCO2 and duration."""
    payload = _post_one_measurement(mock_post, format="discord")

    assert list(payload) == ["embeds"]
    assert len(payload["embeds"]) == 1
    embed = payload["embeds"][0]
    assert "test_function" in embed["title"]
    fields = {field["name"]: field["value"] for field in embed["fields"]}
    assert fields == {"Carbon": "0.005000 gCO2", "Duration": "1.20 s"}


@pytest.mark.parametrize("carbon_limit, expected_color", [
    (None, 0x2ECC71),   # no limit set: green
    (1.0, 0x2ECC71),    # 0.005 gCO2 is below the limit: green
    (0.005, 0xE74C3C),  # equal to the limit counts as over it: red
    (0.001, 0xE74C3C),  # above the limit: red
])
@patch('requests.post')
def test_webhook_exporter_discord_color_follows_carbon_limit(mock_post, carbon_limit, expected_color):
    """The embed is green below carbon_limit (or without one) and red at or above it."""
    payload = _post_one_measurement(mock_post, carbon_emitted=0.005, carbon_limit=carbon_limit, format="discord")

    assert payload["embeds"][0]["color"] == expected_color


@patch('requests.post')
def test_webhook_exporter_slack_sends_block_kit_blocks(mock_post):
    """format="slack" sends Block Kit blocks and a plain text fallback with the function name, gCO2 and duration."""
    payload = _post_one_measurement(mock_post, format="slack")

    assert set(payload) == {"text", "blocks"}
    assert "test_function" in payload["text"]
    assert "0.005000 gCO2" in payload["text"]
    assert "1.20 s" in payload["text"]

    title, metrics = payload["blocks"]
    assert title == {"type": "section", "text": {"type": "plain_text", "text": "EcoTrace: test_function"}}
    assert metrics["type"] == "section"
    assert [field["text"] for field in metrics["fields"]] == ["*Carbon*\n0.005000 gCO2", "*Duration*\n1.20 s"]


@patch('requests.post')
def test_webhook_exporter_unknown_format_falls_back_to_json(mock_post, caplog):
    """An unknown format logs a warning and still sends the default JSON payload."""
    with caplog.at_level("WARNING", logger="ecotrace.exporters.webhook"):
        payload = _post_one_measurement(mock_post, format="teams")

    assert "Invalid format='teams'" in caplog.text
    assert set(payload) == {"function", "carbon_gco2", "duration_s", "region", "run_id", "run_label"}


from ecotrace.exporters.cloud import CloudExporter

@patch('requests.Session.post')
def test_cloud_exporter_registration_and_export(mock_post, tmp_path):
    """Verify CloudExporter formats payload and sends X-EcoTrace-Key header."""
    mock_post.return_value.status_code = 202

    exporter = CloudExporter(api_key="eco_usr_testkey123", retry_dir=str(tmp_path / "queue"))
    try:
        exporter.export(
            carbon_emitted=0.0042,
            func_name="test_cloud_func",
            duration=0.5,
            region="TR",
            run_id="run_123",
            run_label="test_label"
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["function"] == "test_cloud_func"
        assert kwargs["json"]["carbon_gco2"] == 0.0042
        assert kwargs["json"]["region"] == "TR"
        assert kwargs["json"]["run_id"] == "run_123"
        assert exporter.session.headers["X-EcoTrace-Key"] == "eco_usr_testkey123"
    finally:
        exporter.close()

def test_cloud_exporter_requires_key():
    """Verify CloudExporter raises ValueError when instantiated without a valid key."""
    with pytest.raises(ValueError):
        CloudExporter(api_key="")

def test_ecotrace_auto_registers_cloud_exporter():
    """Verify EcoTrace auto-registers CloudExporter when instantiated with eco_usr_ key."""
    eco = EcoTrace(api_key="eco_usr_valid123", quiet=True, check_updates=False)
    assert len(eco._exporters) == 1
    assert isinstance(eco._exporters[0], CloudExporter)
    assert eco._exporters[0].api_key == "eco_usr_valid123"
    eco._exporters[0].close()


# =========================================================================
# Summary exporters: shared test helpers (#183)
# =========================================================================


def _sample_summary(**overrides):
    """A get_summary()-shaped dict with nonzero, distinguishable values."""
    summary = {
        "run_id": "abc123def456",
        "run_label": "nightly-run",
        "duration_s": 12.5,
        "functions_tracked": 3,
        "total_carbon_gco2": 3.21,
        "total_energy_kwh": 0.0125,
        "region": "US",
        "carbon_intensity": 386,
        "intensity_source": "static",
        "budget": None,
        "equivalence": "",
        "hardware": {},
    }
    summary.update(overrides)
    return summary


class _HTMLSummaryParser(HTMLParser):
    """Check the card markup to_html() generates and collect displayed text.

    Only the elements the exporter emits are nesting-checked; any other tag
    (such as one injected through unescaped input) is still recorded in
    ``start_tags``. This is not a general HTML validator and does not
    require XML-compatible HTML. Character references are decoded, so cell
    text is exactly what a browser would display.
    """

    CARD_ELEMENTS = {"div", "table", "caption", "tr", "th", "td"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.start_tags = []
        self.roots = []
        self.rows = []
        self.errors = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.start_tags.append((tag, attrs))
        if tag not in self.CARD_ELEMENTS:
            return
        if not self.open_tags:
            self.roots.append((tag, attrs))
        self.open_tags.append(tag)
        if tag == "tr":
            self.rows.append([])
        elif tag in ("th", "td") and self.rows:
            self.rows[-1].append([tag, ""])

    def handle_endtag(self, tag):
        if tag not in self.CARD_ELEMENTS:
            return
        if not self.open_tags or self.open_tags[-1] != tag:
            self.errors.append(f"unexpected </{tag}>, open: {self.open_tags}")
            return
        self.open_tags.pop()

    def handle_data(self, data):
        if not self.open_tags:
            if data.strip():
                self.errors.append(f"text outside the card: {data!r}")
        elif self.rows and self.rows[-1] and "tr" in self.open_tags:
            self.rows[-1][-1][1] += data


def _parse_html_summary(html_text):
    """Parse to_html() output into (parser, {label: displayed value})."""
    parser = _HTMLSummaryParser()
    parser.feed(html_text)
    parser.close()
    assert not parser.errors, parser.errors
    assert not parser.open_tags, f"unclosed tags: {parser.open_tags}"

    rows = {}
    for row in parser.rows:
        if [cell_tag for cell_tag, _ in row] == ["th", "td"]:
            rows[row[0][1]] = row[1][1]
    return parser, rows


def _markdown_rows(summary):
    """Render with to_markdown() and return {label: cell text}."""
    # Relies on to_markdown()'s fixed two-column "| label | value |" layout
    # and is only called with values that contain no pipes; the escaping
    # tests below assert exact lines instead.
    lines = to_markdown(summary).splitlines()
    return dict(line[2:-2].split(" | ") for line in lines[2:])


def _html_rows(summary):
    """Render with to_html() and return {label: displayed text}."""
    _, rows = _parse_html_summary(to_html(summary))
    return rows


@pytest.fixture(params=["markdown", "html"])
def rendered_rows(request):
    """Render a summary with each exporter; return {label: value}."""
    return {"markdown": _markdown_rows, "html": _html_rows}[request.param]


# =========================================================================
# Summary exporters: behavior shared by to_markdown() and to_html() (#183)
# =========================================================================
# Each test runs once per exporter and asserts the same literal expected
# values for both, so the two formats must display identical values.


def test_summary_formats_metrics_with_units(rendered_rows):
    rows = rendered_rows(_sample_summary())

    assert rows["Total Energy"] == "0.0125000000 kWh"
    assert rows["Duration"] == "12.5000 s"
    assert rows["Total Carbon"] == "3.21000000 gCO₂eq"


def test_summary_shows_small_nonzero_energy_without_rounding_to_zero(
    rendered_rows,
):
    """A ~0.1 s tracked call uses ~1.4e-7 kWh; it must not display as zero."""
    summary = _sample_summary(total_energy_kwh=1.4268757826291852e-07)

    assert rendered_rows(summary)["Total Energy"] == "0.0000001427 kWh"


def test_summary_includes_run_label(rendered_rows):
    rows = rendered_rows(_sample_summary(run_label="nightly-run"))

    assert rows["Run Label"] == "nightly-run"


@pytest.mark.parametrize("run_label", ["", None, "missing"])
def test_summary_shows_na_for_empty_or_missing_run_label(
    rendered_rows, run_label
):
    summary = _sample_summary(run_label=run_label)
    if run_label == "missing":
        del summary["run_label"]

    assert rendered_rows(summary)["Run Label"] == "N/A"


@pytest.mark.parametrize(
    "missing_key, row_label",
    [
        ("total_energy_kwh", "Total Energy"),
        ("duration_s", "Duration"),
        ("total_carbon_gco2", "Total Carbon"),
    ],
)
def test_summary_shows_na_for_missing_or_none_metrics(
    rendered_rows, missing_key, row_label
):
    absent = _sample_summary()
    del absent[missing_key]
    assert rendered_rows(absent)[row_label] == "N/A"

    none_summary = _sample_summary(**{missing_key: None})
    assert rendered_rows(none_summary)[row_label] == "N/A"


def test_summary_shows_zero_values_as_numbers_not_na(rendered_rows):
    summary = _sample_summary(
        total_energy_kwh=0.0, duration_s=0, total_carbon_gco2=0.0
    )
    rows = rendered_rows(summary)

    assert rows["Total Energy"] == "0.0000000000 kWh"
    assert rows["Duration"] == "0.0000 s"
    assert rows["Total Carbon"] == "0.00000000 gCO₂eq"


# =========================================================================
# Summary exporters: to_markdown() structure and escaping (#183)
# =========================================================================


def test_to_markdown_renders_the_exact_table():
    assert to_markdown(_sample_summary()) == (
        "| Metric | Value |\n"
        "| --- | --- |\n"
        "| Run Label | nightly-run |\n"
        "| Total Energy | 0.0125000000 kWh |\n"
        "| Duration | 12.5000 s |\n"
        "| Total Carbon | 3.21000000 gCO₂eq |\n"
    )


@pytest.mark.parametrize(
    "run_label, expected_row",
    [
        ("train|eval", r"| Run Label | train\|eval |"),
        # GFM: "\\" is a literal backslash and "\|" a literal pipe, so the
        # input "a\|b" stays one cell.
        (r"a\|b", r"| Run Label | a\\\|b |"),
        ("line one\nline two", "| Run Label | line one line two |"),
        ("line one\r\nline two", "| Run Label | line one line two |"),
        ("line one\rline two", "| Run Label | line one line two |"),
    ],
    ids=["pipe", "backslash-before-pipe", "lf", "crlf", "cr"],
)
def test_to_markdown_escapes_run_label_into_one_cell(run_label, expected_row):
    lines = to_markdown(_sample_summary(run_label=run_label)).splitlines()

    assert lines[2] == expected_row
    assert len(lines) == 6  # header, separator, four summary rows


# =========================================================================
# Summary exporters: to_html() structure and escaping (#183)
# =========================================================================


def test_to_html_returns_a_standalone_summary_card():
    html_text = to_html(_sample_summary())

    assert isinstance(html_text, str)
    parser, rows = _parse_html_summary(html_text)

    assert len(parser.roots) == 1, "expected one card element wrapping all"
    _, root_attrs = parser.roots[0]
    assert "ecotrace-summary" in (root_attrs.get("class") or "").split()
    assert "table" in [tag for tag, _ in parser.start_tags]
    assert {"Run Label", "Total Energy", "Duration", "Total Carbon"} <= (
        rows.keys()
    )
    for tag, attrs in parser.start_tags:
        assert tag not in {"script", "link", "iframe"}, f"external: <{tag}>"
        assert "src" not in attrs and "href" not in attrs, (tag, attrs)


@pytest.mark.parametrize(
    "run_label, escaped_fragment",
    [
        ("<script>alert('x')</script>", "&lt;script&gt;"),
        ('Tom & "Jerry" <b>bold</b>', "&lt;b&gt;bold&lt;/b&gt;"),
        ('" onmouseover="alert(1)', "&quot; onmouseover=&quot;"),
        ("AT&amp;T", "AT&amp;amp;T"),
    ],
    ids=["script", "markup", "attribute-breakout", "literal-entity"],
)
def test_to_html_escapes_special_characters_in_run_label(
    run_label, escaped_fragment
):
    html_text = to_html(_sample_summary(run_label=run_label))

    # The raw markup carries the escaped form and no executable script...
    assert escaped_fragment in html_text
    assert "<script" not in html_text.lower()
    # ...the browser displays the label literally...
    parser, rows = _parse_html_summary(html_text)
    assert rows["Run Label"] == run_label
    # ...and none of it is interpreted as elements or attributes.
    tags = {tag for tag, _ in parser.start_tags}
    assert not tags & {"script", "b"}
    for tag, attrs in parser.start_tags:
        assert not any(name.startswith("on") for name in attrs), (tag, attrs)

# =========================================================================
# Public imports from ecotrace.exporters (#183)
# =========================================================================


def test_summary_exporters_are_importable_from_package():
    from ecotrace.exporters import summary, to_html, to_markdown

    assert to_markdown is summary.to_markdown
    assert to_html is summary.to_html

    sample = _sample_summary()
    assert "| Total Energy | 0.0125000000 kWh |" in to_markdown(sample)
    assert '<div class="ecotrace-summary">' in to_html(sample)


def test_existing_exporters_still_importable_from_package():
    from ecotrace.exporters import (
        CloudExporter as PackageCloud,
        OTelExporter as PackageOTel,
        WebhookExporter as PackageWebhook,
    )
    from ecotrace.exporters.cloud import CloudExporter as ModuleCloud
    from ecotrace.exporters.otel import OTelExporter as ModuleOTel
    from ecotrace.exporters.webhook import WebhookExporter as ModuleWebhook

    assert PackageCloud is ModuleCloud
    assert PackageOTel is ModuleOTel
    assert PackageWebhook is ModuleWebhook


def test_exporters_package_all_lists_every_public_name():
    import ecotrace.exporters as exporters

    assert set(exporters.__all__) == {
        "CloudExporter",
        "OTelExporter",
        "WebhookExporter",
        "to_html",
        "to_markdown",
    }
    for name in exporters.__all__:
        assert callable(getattr(exporters, name)), name


def test_exporters_package_loads_summary_module_lazily():
    """Importing the package must not import summary.py until it is used."""
    code = (
        "import sys\n"
        "import ecotrace.exporters as exporters\n"
        "assert 'ecotrace.exporters.summary' not in sys.modules\n"
        "exporters.to_html\n"
        "assert 'ecotrace.exporters.summary' in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_exporters_package_rejects_unknown_names():
    import ecotrace.exporters as exporters

    with pytest.raises(AttributeError):
        exporters.to_pdf


# =========================================================================
# End-to-end: real get_summary() -> summary exporters (#183)
# =========================================================================


def test_real_get_summary_renders_in_markdown_and_html(monkeypatch, tmp_path):
    """Feed a real EcoTrace session summary through both exporters.

    Runs offline: no GPU, live grid API, cloud exporter or update check.
    """
    for env_var in (
        "ECOTRACE_GRID_API_KEY", "ECOTRACE_CLOUD_KEY", "GEMINI_API_KEY"
    ):
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.chdir(tmp_path)  # the audit-log CSV is written to the cwd

    with patch("ecotrace.core.get_all_gpu_info", return_value=[]), \
            patch("ecotrace.core.load_cli_config", return_value={}):
        eco = EcoTrace(
            region_code="US",
            check_updates=False,
            quiet=True,
            run_label="integration-run",
        )
    assert eco._exporters == []  # no cloud exporter was registered

    eco._accumulate_carbon(0.5, "integration_func", 1.0)
    summary = eco.get_summary()

    assert "total_energy_kwh" in summary
    assert summary["total_energy_kwh"] == pytest.approx(
        0.5 / eco.carbon_intensity
    )
    assert summary["total_energy_kwh"] > 0

    expected = {
        "Run Label": "integration-run",
        "Total Energy": f"{summary['total_energy_kwh']:.10f} kWh",
        "Duration": f"{summary['duration_s']:.4f} s",
        "Total Carbon": "0.50000000 gCO₂eq",
    }
    assert _markdown_rows(summary) == expected
    assert _html_rows(summary) == expected
    assert expected["Total Energy"] != "0.0000000000 kWh"
