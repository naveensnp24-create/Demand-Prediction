/**
 * API client service
 */

export const API_URL = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')

/**
 * Make an API request with automatic error handling
 * @param path - API endpoint path
 * @param options - Fetch options
 * @returns Promise resolving to the response data
 * @throws Error with user-friendly message if request fails
 */
export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options)
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const detail = payload?.detail
    throw new Error(
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((item: string | { msg?: string }) =>
                typeof item === 'string' ? item : item.msg,
              )
              .join('; ')
          : `Request failed (${response.status}). Check that the API server is running.`,
    )
  }

  return payload as T
}
