export type ThemePreference = 'system' | 'light' | 'dark'

export const resolveTheme = (preference: ThemePreference = 'system'): 'light' | 'dark' => {
  if (preference === 'dark' || preference === 'light') return preference
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const applyDocumentTheme = (preference: ThemePreference = 'system'): 'light' | 'dark' => {
  const resolved = resolveTheme(preference)
  document.documentElement.classList.toggle('app-dark', resolved === 'dark')
  document.documentElement.dataset.themePreference = preference
  return resolved
}
