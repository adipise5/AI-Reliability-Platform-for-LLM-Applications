"""Renders an experiment comparison as a PDF via fpdf2 — a pure-Python
library with no system-level dependencies (no wkhtmltopdf, no Cairo/Pango),
which keeps this service's Docker image and local setup simple."""

from __future__ import annotations

from fpdf import FPDF

from report_generator.domain.entities import RemoteExperimentComparison, ReportFormat


class PdfReportRenderer:
    format = ReportFormat.PDF

    def render(self, comparison: RemoteExperimentComparison) -> bytes:
        experiment = comparison.experiment
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, experiment.name, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, experiment.description or "(no description)")
        pdf.ln(2)
        pdf.cell(0, 6, f"{len(comparison.runs)} run(s)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        col_widths = (55, 55, 35, 25, 20)
        headers = ("Run ID", "Prompt ID", "Model", "Status", "Score")
        pdf.set_font("Helvetica", "B", 9)
        for header, width in zip(headers, col_widths, strict=True):
            pdf.cell(width, 8, header, border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for run in comparison.runs:
            score = f"{run.aggregate_score:.4f}" if run.aggregate_score is not None else "-"
            values = (str(run.id)[:18], str(run.prompt_id)[:18], run.model[:20], run.status, score)
            for value, width in zip(values, col_widths, strict=True):
                pdf.cell(width, 8, value, border=1)
            pdf.ln()

        return bytes(pdf.output())
