from __future__ import annotations

from uuid import uuid4

import httpx
import pytest
import respx

from dashboard_backend.domain.errors import ReportNotFoundError, UpstreamServiceError
from dashboard_backend.infrastructure.clients.report_generator_client import HttpReportReader

BASE_URL = "http://report-generator.internal"


def _report_payload(report_id, **overrides):
    payload = {
        "id": str(report_id),
        "org_id": str(uuid4()),
        "experiment_id": str(uuid4()),
        "format": "html",
        "status": "ready",
        "error_message": None,
        "created_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:01:00Z",
    }
    payload.update(overrides)
    return payload


@respx.mock
async def test_list_reports_parses_a_bare_list_and_sends_experiment_id():
    experiment_id = uuid4()
    route = respx.get(f"{BASE_URL}/api/v1/reports").mock(
        return_value=httpx.Response(200, json=[_report_payload(uuid4())])
    )
    client = HttpReportReader(BASE_URL, timeout=5.0)

    reports = await client.list_reports("tok", experiment_id=experiment_id)

    assert len(reports) == 1
    assert route.calls.last.request.url.params["experiment_id"] == str(experiment_id)


@respx.mock
async def test_list_reports_raises_upstream_error_on_5xx():
    respx.get(f"{BASE_URL}/api/v1/reports").mock(return_value=httpx.Response(500))
    client = HttpReportReader(BASE_URL, timeout=5.0)

    with pytest.raises(UpstreamServiceError):
        await client.list_reports("tok")


@respx.mock
async def test_get_report_parses_the_response():
    report_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/reports/{report_id}").mock(
        return_value=httpx.Response(200, json=_report_payload(report_id))
    )
    client = HttpReportReader(BASE_URL, timeout=5.0)

    report = await client.get_report("tok", report_id)

    assert report.id == report_id


@respx.mock
async def test_get_report_raises_not_found_on_404():
    report_id = uuid4()
    respx.get(f"{BASE_URL}/api/v1/reports/{report_id}").mock(return_value=httpx.Response(404))
    client = HttpReportReader(BASE_URL, timeout=5.0)

    with pytest.raises(ReportNotFoundError):
        await client.get_report("tok", report_id)
