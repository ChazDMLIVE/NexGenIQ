/// <reference types="vite/client" />

// Type declarations for the NexGenIQ frontend's build-time environment
// variables (Vite exposes any variable prefixed with VITE_).

interface ImportMetaEnv {
  /**
   * Base URL of the NexGenIQ backend API. Empty in development (the Vite
   * dev server proxies /api to localhost); set to the deployed backend's
   * URL in a production build.
   */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
