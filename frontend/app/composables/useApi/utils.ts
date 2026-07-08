/** Shared API base URL resolver */
export function useApiBase() {
  const config = useRuntimeConfig()
  return config.public.apiBase || 'http://localhost:8000'
}
