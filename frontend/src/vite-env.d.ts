//frontend/src/vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // add other env vars here...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
