export interface SessionUser {
  id: number
  username: string
  first_name: string
  last_name: string
}

export interface StoredSession {
  token: string
  user: SessionUser
}

const SESSION_KEY = 'money_management_user'

export const getStoredSession = (): StoredSession | null => {
  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw)
    if (parsed?.token && parsed?.user) {
      return parsed as StoredSession
    }
  } catch (error) {
    console.warn('Invalid saved session data found; clearing local session.', error)
  }

  localStorage.removeItem(SESSION_KEY)
  return null
}

export const setStoredSession = (session: StoredSession): void => {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
}

export const clearStoredSession = (): void => {
  localStorage.removeItem(SESSION_KEY)
}
