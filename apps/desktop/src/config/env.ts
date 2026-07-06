const DEFAULT_API_URL = 'http://localhost:8001'

export function getApiUrl(): string {
  return import.meta.env.VITE_NOVA_API_URL?.trim() || DEFAULT_API_URL
}

export function isMockMode(): boolean {
  return import.meta.env.VITE_USE_MOCKS === 'true'
}

export function getWebSocketUrl(path: string): string {
  const base = getApiUrl().replace(/^http/, 'ws')
  return `${base}${path}`
}
