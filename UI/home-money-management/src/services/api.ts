import axios from 'axios'
import { clearStoredSession, getStoredSession } from './session'

const DEFAULT_API_BASE_URL = '/api'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/+$/, '')

axios.defaults.baseURL = API_BASE_URL

const withTrailingSlash = (url: string): string => {
  if (!url.startsWith('/') || url.endsWith('/')) return url

  const hashIndex = url.indexOf('#')
  const hash = hashIndex >= 0 ? url.slice(hashIndex) : ''
  const withoutHash = hashIndex >= 0 ? url.slice(0, hashIndex) : url
  const queryIndex = withoutHash.indexOf('?')
  const query = queryIndex >= 0 ? withoutHash.slice(queryIndex) : ''
  const path = queryIndex >= 0 ? withoutHash.slice(0, queryIndex) : withoutHash

  if (!path || path.endsWith('/') || /\.[^/]+$/.test(path)) {
    return url
  }

  return `${path}/${query}${hash}`
}

axios.interceptors.request.use((config) => {
  const session = getStoredSession()
  if (session?.token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = config.headers.Authorization ?? `Token ${session.token}`
  }
  if (typeof config.url === 'string') {
    config.url = withTrailingSlash(config.url)
  }
  return config
})

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export async function getAllPages<T>(
  url: string,
  selectItems: (data: PaginatedResponse<T> & Record<string, unknown>) => T[],
  params: Record<string, unknown> = {},
): Promise<T[]> {
  const items: T[] = []
  let nextPage: string | null = url
  let firstRequest = true

  while (nextPage) {
    const response = await axios.get(nextPage, {
      params: firstRequest ? { ...params, page_size: 100 } : {},
    }) as { data: PaginatedResponse<T> & Record<string, unknown> }
    items.push(...selectItems(response.data))
    nextPage = response.data.next || null
    firstRequest = false
  }
  return items
}

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      clearStoredSession()
    }
    return Promise.reject(error)
  },
)

export default axios
