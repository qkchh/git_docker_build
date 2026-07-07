export function buildsData() {
  return {
    builds: [],
    activeBuild: null,
    buildLog: [],
    logModal: null,

    buildStatusClass(status) {
      const map = {
        running:   'bg-yellow-400/10 text-yellow-400 ring-1 ring-yellow-400/30',
        success:   'bg-green-400/10 text-green-400 ring-1 ring-green-400/30',
        failed:    'bg-red-400/10 text-red-400 ring-1 ring-red-400/30',
        pending:   'bg-gray-400/10 text-gray-400 ring-1 ring-gray-400/30',
        cancelled: 'bg-gray-500/10 text-gray-500 ring-1 ring-gray-500/30',
      }
      return map[status] || map.pending
    },

    async cancelBuild() {
      if (!this.activeBuild) return
      await this.apiFetch(`/api/builds/${this.activeBuild.id}/cancel`, { method: 'POST' })
    },

    async triggerBuild(repo, commit) {
      const r = await this.apiFetch('/api/builds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repo.id, commit_sha: commit.sha, commit_message: commit.message }),
      })
      if (!r.ok) { this.showToast(this.t('err_create_build')); return }
      const build = await r.json()
      this.currentTab = 'builds'
      this.activeBuild = build
      this.buildLog = []
      await this.streamBuild(build)
      await this.loadBuilds()
    },

    async streamBuild(build) {
      // fetch supports the auth header, so the token never appears in URLs or access logs.
      const response = await this.apiFetch(`/api/builds/${build.id}/stream`)
      if (!response.ok || !response.body) {
        this.showToast(this.t('err_create_build'))
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const appendLine = (line) => {
        this.buildLog.push(line)
        this.$nextTick(() => {
          const box = this.$refs.logBox
          if (box) box.scrollTop = box.scrollHeight
        })
        if (line === '[DONE] All done') {
          this.activeBuild = { ...this.activeBuild, status: 'success' }
        } else if (line.startsWith('[ERROR]')) {
          this.activeBuild = { ...this.activeBuild, status: 'failed' }
        } else if (line.startsWith('[CANCELLED]')) {
          this.activeBuild = { ...this.activeBuild, status: 'cancelled' }
        }
      }

      while (true) {
        const { value, done } = await reader.read()
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
        const messages = buffer.split('\n\n')
        buffer = messages.pop() || ''
        for (const message of messages) {
          const data = message.split('\n').find(line => line.startsWith('data: '))
          if (data) appendLine(JSON.parse(data.slice(6)))
        }
        if (done) break
      }
    },

    async loadBuilds() {
      const r = await this.apiFetch('/api/builds')
      if (r.ok) this.builds = await r.json()
    },

    scrollBuildLogToBottom() {
      this.$nextTick(() => requestAnimationFrame(() => {
        const box = this.$refs.buildLogScroll
        if (box) box.scrollTop = box.scrollHeight
      }))
    },

    showBuildLog(build) {
      this.logModal = build
      this.scrollBuildLogToBottom()
    },
  }
}
