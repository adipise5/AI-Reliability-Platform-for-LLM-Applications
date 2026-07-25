from __future__ import annotations

from dataclasses import replace

from report_generator.infrastructure.renderers.html_renderer import HtmlReportRenderer
from tests.unit.conftest import make_comparison


def test_renders_experiment_name_and_run_rows():
    comparison = make_comparison(run_count=2)
    renderer = HtmlReportRenderer()

    html = renderer.render(comparison).decode("utf-8")

    assert comparison.experiment.name in html
    for run in comparison.runs:
        assert str(run.id) in html
    assert html.count("<tr>") == 3  # 1 header row + 2 data rows


def test_renders_placeholder_row_when_no_runs():
    comparison = make_comparison(run_count=0)
    renderer = HtmlReportRenderer()

    html = renderer.render(comparison).decode("utf-8")

    assert "No runs attached" in html


def test_escapes_html_in_experiment_fields():
    comparison = make_comparison(run_count=0)
    comparison = replace(comparison, experiment=replace(comparison.experiment, name="<script>x"))
    renderer = HtmlReportRenderer()

    html = renderer.render(comparison).decode("utf-8")

    assert "<script>x" not in html
    assert "&lt;script&gt;" in html
