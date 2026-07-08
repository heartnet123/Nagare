/** API response wrapper */
export interface ApiListResponse<T> {
  sessions: T[]
  total: number
}

/** Generic API error from FastAPI */
export interface ApiError {
  detail: string
}
