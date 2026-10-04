import type { H3Event } from 'h3'

export interface ApiError {
  error: { code: string, message: string }
}

/** Sends `{ error: { code, message } }` with an HTTP status (handoff section 5). */
export function apiError(event: H3Event, status: number, code: string, message: string): ApiError {
  setResponseStatus(event, status)
  return { error: { code, message } }
}
