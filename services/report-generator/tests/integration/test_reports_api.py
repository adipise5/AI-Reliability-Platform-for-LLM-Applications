from __future__ import annotations

from uuid import uuid4

from report_generator.domain.entities import ReportFormat, ReportStatus
from tests.unit.conftest import make_report


def test_request_report_requires_authentication(app):
    from fastapi.testclient import TestClient

    unauthenticated_client = TestClient(app)

    response = unauthenticated_client.post("/api/v1/reports", json={"experiment_id": str(uuid4())})

    assert response.status_code == 401


def test_request_report_returns_202_and_enqueues(client, queue):
    experiment_id = uuid4()

    response = client.post(
        "/api/v1/reports", json={"experiment_id": str(experiment_id), "format": "pdf"}
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["format"] == "pdf"
    assert len(queue.enqueued) == 1


def test_get_report_returns_404_for_unknown_id(client):
    response = client.get(f"/api/v1/reports/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["type"] == "report_not_found"


def test_get_and_list_round_trip(client, org_id, repo):
    experiment_id = uuid4()
    created = client.post(
        "/api/v1/reports", json={"experiment_id": str(experiment_id), "format": "html"}
    ).json()

    fetched = client.get(f"/api/v1/reports/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    listed = client.get("/api/v1/reports", params={"experiment_id": str(experiment_id)})
    assert listed.status_code == 200
    assert [r["id"] for r in listed.json()] == [created["id"]]


def test_get_report_content_returns_409_when_not_ready(client):
    experiment_id = uuid4()
    created = client.post(
        "/api/v1/reports", json={"experiment_id": str(experiment_id), "format": "html"}
    ).json()

    response = client.get(f"/api/v1/reports/{created['id']}/content")

    assert response.status_code == 409
    assert response.json()["type"] == "report_not_ready"


def test_get_report_content_returns_the_bytes_when_ready(client, org_id, repo):
    report = make_report(
        org_id=org_id, status=ReportStatus.READY, content=b"<html>done</html>"
    )
    repo.reports[report.id] = report

    response = client.get(f"/api/v1/reports/{report.id}/content")

    assert response.status_code == 200
    assert response.content == b"<html>done</html>"
    assert response.headers["content-type"].startswith("text/html")


def test_get_report_content_pdf_media_type(client, org_id, repo):
    report = make_report(
        org_id=org_id, status=ReportStatus.READY, content=b"%PDF-1.4", format=ReportFormat.PDF
    )
    repo.reports[report.id] = report

    response = client.get(f"/api/v1/reports/{report.id}/content")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
