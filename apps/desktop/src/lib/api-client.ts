import type { ErrorResponse } from '@nova/api-contracts'
import { getApiUrl } from '@/config/env'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ErrorResponse
    if (body.error) {
      return new ApiError(response.status, body.error.code, body.error.message)
    }
  } catch {
    // fall through
  }
  return new ApiError(response.status, `http_${response.status}`, response.statusText || 'Request failed')
}

export async function apiGet<T>(path: string, searchParams?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, getApiUrl())
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const response = await fetch(url.toString())
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  return (await response.json()) as T
}

export async function apiPost<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const url = new URL(path, getApiUrl())
  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  return (await response.json()) as TRes
}

export async function apiPatch<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const url = new URL(path, getApiUrl())
  const response = await fetch(url.toString(), {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  return (await response.json()) as TRes
}

export async function apiDelete<TRes>(path: string): Promise<TRes> {
  const url = new URL(path, getApiUrl())
  const response = await fetch(url.toString(), { method: 'DELETE' })
  if (!response.ok) {
    throw await parseErrorResponse(response)
  }
  return (await response.json()) as TRes
}
