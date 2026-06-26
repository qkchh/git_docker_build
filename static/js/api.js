export function apiData() {
  return {
    // Unified fetch with auth header; auto-logout on 401
    async apiFetch(url, options = {}) {
      options.headers = { ...options.headers, 'X-Access-Token': this.token }
      const r = await fetch(url, options)
      if (r.status === 401) { this.logout(); return r }
      return r
    },
  }
}
