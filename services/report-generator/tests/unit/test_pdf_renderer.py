from __future__ import annotations

from report_generator.infrastructure.renderers.pdf_renderer import PdfReportRenderer
from tests.unit.conftest import make_comparison


def test_renders_non_empty_pdf_bytes():
    comparison = make_comparison(run_count=2)
    renderer = PdfReportRenderer()

    content = renderer.render(comparison)

    assert isinstance(content, bytes)
    assert content.startswith(b"%PDF-")
    assert len(content) > 0


def test_renders_pdf_with_no_runs():
    comparison = make_comparison(run_count=0)
    renderer = PdfReportRenderer()

    content = renderer.render(comparison)

    assert content.startswith(b"%PDF-")
