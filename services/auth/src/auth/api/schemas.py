"""API-facing request/response models — see the gateway's schemas.py for
why these are kept separate from the domain dataclasses."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from auth.domain.entities import ApiKey, Org, Principal, User


class RegisterOrgIn(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=200)
    owner_email: EmailStr
    owner_password: str = Field(..., min_length=8)


class RegisterOrgOut(BaseModel):
    org_id: UUID
    org_name: str
    owner_id: UUID
    owner_email: str

    @classmethod
    def from_domain(cls, org: Org, owner: User) -> RegisterOrgOut:
        return cls(org_id=org.id, org_name=org.name, owner_id=owner.id, owner_email=owner.email)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class IntrospectIn(BaseModel):
    credential: str = Field(..., min_length=1)


class IntrospectOut(BaseModel):
    subject: str
    org_id: str
    scopes: list[str]

    @classmethod
    def from_domain(cls, principal: Principal) -> IntrospectOut:
        return cls(subject=principal.subject, org_id=str(principal.org_id), scopes=sorted(principal.scopes))


class CreateApiKeyIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scopes: list[str] | None = Field(
        default=None, description="Defaults to the creator's own scopes if omitted."
    )


class CreateApiKeyOut(BaseModel):
    id: UUID
    name: str
    prefix: str
    secret: str = Field(..., description="Only ever shown once, at creation time.")
    scopes: list[str]

    @classmethod
    def from_domain(cls, api_key: ApiKey, secret: str) -> CreateApiKeyOut:
        return cls(
            id=api_key.id,
            name=api_key.name,
            prefix=api_key.prefix,
            secret=secret,
            scopes=sorted(api_key.scopes),
        )


class ErrorOut(BaseModel):
    type: str
    message: str
