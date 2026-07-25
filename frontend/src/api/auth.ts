import { request } from "./client";
import type { LoginResponse, RegisterOrgResponse } from "./types";

const AUTH_URL = import.meta.env.VITE_AUTH_URL;

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>(AUTH_URL, "/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function registerOrg(
  orgName: string,
  ownerEmail: string,
  ownerPassword: string,
): Promise<RegisterOrgResponse> {
  return request<RegisterOrgResponse>(AUTH_URL, "/api/v1/orgs", {
    method: "POST",
    body: { org_name: orgName, owner_email: ownerEmail, owner_password: ownerPassword },
  });
}
