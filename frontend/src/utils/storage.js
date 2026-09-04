const PREFIX = 'campus_'

export const STORAGE_KEYS = {
  TOKEN: `${PREFIX}token`,
  USER: `${PREFIX}user`,
  REMEMBER_USER: `${PREFIX}remember_user`
}

function safeParse(str) {
  if (!str) return null
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}

export const storage = {
  getToken() {
    return localStorage.getItem(STORAGE_KEYS.TOKEN) || ''
  },
  setToken(token) {
    localStorage.setItem(STORAGE_KEYS.TOKEN, token)
  },
  removeToken() {
    localStorage.removeItem(STORAGE_KEYS.TOKEN)
  },

  getUser() {
    return safeParse(localStorage.getItem(STORAGE_KEYS.USER))
  },
  setUser(user) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user))
  },
  removeUser() {
    localStorage.removeItem(STORAGE_KEYS.USER)
  },

  getRememberUser() {
    return localStorage.getItem(STORAGE_KEYS.REMEMBER_USER) || ''
  },
  setRememberUser(username) {
    localStorage.setItem(STORAGE_KEYS.REMEMBER_USER, username)
  },
  removeRememberUser() {
    localStorage.removeItem(STORAGE_KEYS.REMEMBER_USER)
  },

  clearAuth() {
    this.removeToken()
    this.removeUser()
  }
}
