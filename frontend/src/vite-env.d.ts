/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_URL: string;
  readonly VITE_DASHBOARD_URL: string;
  readonly VITE_REPORT_GENERATOR_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
