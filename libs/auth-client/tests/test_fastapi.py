from __future__ import annotations

from typing import Annotated

import httpx
import respx
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from auth_client.client import AuthServiceClient
from auth_client.fastapi import RequirePrincipal
from auth_client.models import IntrospectionResult

BASE_URL = "http://auth.internal"

# Module-level, deliberately: FastAPI resolves `Annotated[..., Depends(require_principal)]`
# via `typing.get_type_hints()` against the route function's *module globals* (this file
# uses `from __future__ import annotations`, which stringifies annotations). A
# `Depends(...)` default referencing a name that only exists in an enclosing closure
# — e.g. a local variable inside a `build_app()` helper — fails to resolve.
require_principal = RequirePrincipal(AuthServiceClient(BASE_URL))

app = FastAPI()


@app.get("/whoami")
async def whoami(
    principal: Annotated[IntrospectionResult, Depends(require_principal)],
) -> dict[str, str]:
    return {"subject": principal.subject}


@respx.mock
def test_returns_401_when_no_bearer_token_present():
    client = TestClient(app)

    response = client.get("/whoami")

    assert response.status_code == 401


@respx.mock
def test_returns_200_with_subject_on_valid_credential():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(
        return_value=httpx.Response(200, json={"subject": "user:1", "org_id": "org:1", "scopes": []})
    )
    client = TestClient(app)

    response = client.get("/whoami", headers={"Authorization": "Bearer good-token"})

    assert response.status_code == 200
    assert response.json() == {"subject": "user:1"}


@respx.mock
def test_returns_401_when_auth_service_rejects_credential():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(return_value=httpx.Response(401))
    client = TestClient(app)

    response = client.get("/whoami", headers={"Authorization": "Bearer bad-token"})

    assert response.status_code == 401


@respx.mock
def test_returns_503_when_auth_service_is_unreachable():
    respx.post(f"{BASE_URL}/api/v1/auth/introspect").mock(side_effect=httpx.ConnectError("refused"))
    client = TestClient(app)

    response = client.get("/whoami", headers={"Authorization": "Bearer whatever"})

    assert response.status_code == 503
