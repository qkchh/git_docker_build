export function containersData() {
  return {
    containers: [],
    containerLogModal: null,
    containerLogsRefreshing: false,

    async loadContainers() {
      const r = await this.apiFetch('/api/containers')
      if (r.ok) this.containers = await r.json()
    },

    async viewContainerLogs(c) {
      const r = await this.apiFetch(`/api/containers/${c.id}/logs`)
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      const { logs } = await r.json()
      this.containerLogModal = { id: c.id, name: c.name, logs: logs || this.t('no_container_logs') }
    },

    async refreshContainerLogs() {
      if (!this.containerLogModal || this.containerLogsRefreshing) return
      this.containerLogsRefreshing = true
      try {
        const r = await this.apiFetch(`/api/containers/${this.containerLogModal.id}/logs`)
        if (!r.ok) { const e = await r.json(); alert(e.detail); return }
        const { logs } = await r.json()
        this.containerLogModal = { ...this.containerLogModal, logs: logs || this.t('no_container_logs') }
      } finally {
        this.containerLogsRefreshing = false
      }
    },

    async containerAction(id, action) {
      if (action === 'remove' && !confirm(this.t('confirm_remove_container'))) return
      const r = await this.apiFetch(`/api/containers/${id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      })
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      await this.loadContainers()
    },
  }
}
