"""Renders an experiment comparison as a single self-contained HTML page —
no templating engine, since the layout is simple enough that a template
file would just be indirection without benefit."""

from __future__ import annotations

from html import escape

from report_generator.domain.entities import (
    RemoteExperimentComparison,
    RemoteRunSummary,
    ReportFormat,
)


class HtmlReportRenderer:
    format = ReportFormat.HTML

    def render(self, comparison: RemoteExperimentComparison) -> bytes:
        experiment = comparison.experiment
        rows = "\n".join(_run_row(run) for run in comparison.runs) or (
            '<tr><td colspan="5">No runs attached to this experiment yet.</td></tr>'
        )
        html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{escape(experiment.name)} — Eval Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ border: 1px solid #ccc; padding: 0.5rem 0.75rem; text-align: left; }}
  th {{ background: #f4f4f4; }}
</style>
</head>
<body>
<h1>{escape(experiment.name)}</h1>
<p>{escape(experiment.description)}</p>
<p>{len(comparison.runs)} run(s)</p>
<table>
<thead>
<tr><th>Run ID</th><th>Prompt ID</th><th>Model</th><th>Status</th><th>Score</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""
        return html.encode("utf-8")


def _run_row(run: RemoteRunSummary) -> str:
    score = f"{run.aggregate_score:.4f}" if run.aggregate_score is not None else "—"
    return (
        "<tr>"
        f"<td>{escape(str(run.id))}</td>"
        f"<td>{escape(str(run.prompt_id))}</td>"
        f"<td>{escape(run.model)}</td>"
        f"<td>{escape(run.status)}</td>"
        f"<td>{escape(score)}</td>"
        "</tr>"
    )
