import { useCallback, useEffect, useState } from 'react'
import { api } from '@/services/api'

/**
 * Custom hook for fetching and managing API data
 * @param path - API endpoint path (null to skip fetching)
 * @returns Object containing data, error, loading state, and refresh function
 */
export function useData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [revision, setRevision] = useState(0)

  const refresh = useCallback(() => setRevision((value) => value + 1), [])

  useEffect(() => {
    setData(null)
    setError('')

    if (!path) {
      setLoading(false)
      return
    }

    const controller = new AbortController()
    setLoading(true)

    api<T>(path, { signal: controller.signal })
      .then(setData)
      .catch((reason: Error) => {
        if (!controller.signal.aborted)
          setError(reason.message || 'Unable to reach the API server.')
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [path, revision])

  return { data, error, loading, refresh }
}
