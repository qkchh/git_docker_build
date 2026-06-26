export function authData() {
  return {
    isAuthenticated: false,
    token: '',
    tokenInput: '',
    authError: '',

    _loadAuth() {
      try {
        const raw = localStorage.getItem('gdb_auth')
        if (!raw) return
        const { token, expiry } = JSON.parse(raw)
        if (Date.now() < expiry) {
          this.token = token
          this.isAuthenticated = true
        } else {
          localStorage.removeItem('gdb_auth')
        }
      } catch { localStorage.removeItem('gdb_auth') }
    },

    async submitToken() {
      this.authError = ''
      const t = this.tokenInput.trim()
      if (!t) return
      const r = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: t }),
      })
      if (r.ok) {
        this.token = t
        this.tokenInput = ''
        this.isAuthenticated = true
        const expiry = Date.now() + 30 * 24 * 60 * 60 * 1000  // 30 days
        localStorage.setItem('gdb_auth', JSON.stringify({ token: t, expiry }))
        await this.loadRepos()
      } else {
        this.authError = this.lang === 'zh' ? 'Token 无效' : 'Invalid token'
      }
    },

    logout() {
      localStorage.removeItem('gdb_auth')
      this.token = ''
      this.isAuthenticated = false
    },
  }
}
