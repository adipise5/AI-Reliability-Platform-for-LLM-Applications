from __future__ import annotations

from uuid import uuid4

from tests.unit.conftest import make_report


def test_list_reports_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.get("/api/v1/reports")

    assert response.status_code == 401


def test_list_reports_returns_reports(client, report_reader):
    report = make_report()
    report_reader.reports[report.id] = report

    response = client.get("/api/v1/reports")

    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == [str(report.id)]


def test_get_report_returns_404_for_unknown_id(client):
    response = client.get(f"/api/v1/reports/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "report_not_found"


def test_get_report_returns_the_report(client, report_reader):
    report = make_report()
    report_reader.reports[report.id] = report

    response = client.get(f"/api/v1/reports/{report.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(report.id)
