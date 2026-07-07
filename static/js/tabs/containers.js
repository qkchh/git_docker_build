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
      if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
      const { logs } = await r.json()
      this.containerLogModal = { id: c.id, name: c.name, logs: logs || this.t('no_container_logs') }
      this.scrollContainerLogToBottom()
    },

    async refreshContainerLogs() {
      if (!this.containerLogModal || this.containerLogsRefreshing) return
      this.containerLogsRefreshing = true
      try {
        const r = await this.apiFetch(`/api/containers/${this.containerLogModal.id}/logs`)
        if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
        const { logs } = await r.json()
        this.containerLogModal = { ...this.containerLogModal, logs: logs || this.t('no_container_logs') }
        this.scrollContainerLogToBottom()
      } finally {
        this.containerLogsRefreshing = false
      }
    },

    scrollContainerLogToBottom() {
      this.$nextTick(() => requestAnimationFrame(() => {
        const box = this.$refs.containerLogScroll
        if (box) box.scrollTop = box.scrollHeight
      }))
    },

    async containerAction(id, action) {
      const doAction = async () => {
        const r = await this.apiFetch(`/api/containers/${id}/action`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action }),
        })
        if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
        await this.loadContainers()
      }
      if (action === 'remove') {
        this.showConfirm(this.t('confirm_remove_container'), doAction)
      } else {
        await doAction()
      }
    },
  }
}
