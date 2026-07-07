export function reposData() {
  return {
    // Repos state
    repos: [],
    showAddRepo: false,
    newRepo: { name: '', source_type: 'remote', git_url: '', local_path: '' },
    formError: '',

    // Commits panel state
    selectedRepo: null,
    commits: [],
    repoBranches: [],
    selectedBranch: '',
    loadingCommits: false,

    // Env vars panel state
    selectedEnvRepo: null,
    envVars: [],
    newEnvKey: '',
    newEnvVal: '',
    showPasteArea: false,
    pasteContent: '',
    importMsg: '',
    editingEnvId: null,
    editingEnvKey: '',
    editingEnvVal: '',

    // ================================================================
    // Repos
    // ================================================================
    async loadRepos() {
      const r = await this.apiFetch('/api/repos')
      if (r.ok) this.repos = await r.json()
    },

    resetNewRepo() {
      this.newRepo = { name: '', source_type: 'remote', git_url: '', local_path: '' }
      this.formError = ''
    },

    async createRepo() {
      this.formError = ''
      const payload = { ...this.newRepo }
      if (payload.source_type === 'remote') delete payload.local_path
      else delete payload.git_url

      const r = await this.apiFetch('/api/repos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!r.ok) {
        const err = await r.json()
        this.formError = err.detail || this.t('err_save_repo')
        return
      }
      this.showAddRepo = false
      this.resetNewRepo()
      await this.loadRepos()
    },

    async deleteRepo(id) {
      this.showConfirm(this.t('confirm_delete_repo'), async () => {
        await this.apiFetch(`/api/repos/${id}`, { method: 'DELETE' })
        if (this.selectedRepo?.id === id) { this.selectedRepo = null; this.commits = [] }
        await this.loadRepos()
      })
    },

    // ================================================================
    // Commits
    // ================================================================
    async openRepo(repo) {
      this.selectedRepo = repo
      this.selectedBranch = ''
      await this.loadCommits(repo)
    },

    visibleCommits() {
      if (!this.selectedBranch) return this.commits
      return this.commits.filter(commit => (commit.branches || []).includes(this.selectedBranch))
    },

    async loadCommits(repo) {
      this.loadingCommits = true
      this.commits = []
      try {
        const [commitsResponse, branchesResponse] = await Promise.all([
          this.apiFetch(`/api/repos/${repo.id}/commits`),
          this.apiFetch(`/api/repos/${repo.id}/branches`),
        ])
        if (commitsResponse.ok) this.commits = await commitsResponse.json()
        else { const err = await commitsResponse.json(); this.showToast(err.detail || this.t('err_load_commits')) }
        if (branchesResponse.ok) this.repoBranches = await branchesResponse.json()
      } finally {
        this.loadingCommits = false
      }
    },

    // ================================================================
    // Env Vars
    // ================================================================
    async openEnvPanel(repo) {
      if (this.selectedEnvRepo?.id === repo.id) {
        this.selectedEnvRepo = null; this.envVars = []; return
      }
      this.selectedEnvRepo = repo
      await this.loadEnvVars(repo)
    },

    async loadEnvVars(repo) {
      const r = await this.apiFetch(`/api/repos/${repo.id}/envs`)
      if (r.ok) this.envVars = await r.json()
    },

    async addEnvVar() {
      const key = this.newEnvKey.trim()
      if (!key) return
      const r = await this.apiFetch(`/api/repos/${this.selectedEnvRepo.id}/envs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value: this.newEnvVal }),
      })
      if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
      this.newEnvKey = ''; this.newEnvVal = ''
      await this.loadEnvVars(this.selectedEnvRepo)
    },

    async deleteEnvVar(env) {
      await this.apiFetch(`/api/repos/${this.selectedEnvRepo.id}/envs/${env.id}`, { method: 'DELETE' })
      await this.loadEnvVars(this.selectedEnvRepo)
    },

    startEditEnv(env) {
      this.editingEnvId = env.id
      this.editingEnvKey = env.key
      this.editingEnvVal = env.value
    },

    cancelEditEnv() {
      this.editingEnvId = null
      this.editingEnvKey = ''
      this.editingEnvVal = ''
    },

    async saveEditEnv(env) {
      const key = this.editingEnvKey.trim()
      if (!key) return
      const r = await this.apiFetch(`/api/repos/${this.selectedEnvRepo.id}/envs/${env.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value: this.editingEnvVal }),
      })
      if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
      this.cancelEditEnv()
      await this.loadEnvVars(this.selectedEnvRepo)
    },

    async bulkImportEnv() {
      const content = this.pasteContent.trim()
      if (!content) return
      const r = await this.apiFetch(`/api/repos/${this.selectedEnvRepo.id}/envs/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })
      if (!r.ok) { const e = await r.json(); this.showToast(e.detail); return }
      const { imported } = await r.json()
      this.pasteContent = ''; this.showPasteArea = false
      this.importMsg = `${this.t('import_success')} ${imported} ${this.t('import_unit')}`
      setTimeout(() => { this.importMsg = '' }, 3000)
      await this.loadEnvVars(this.selectedEnvRepo)
    },

    exportEnvFile() {
      const lines = this.envVars.map(e => `${e.key}=${e.value}`).join('\n') + '\n'
      const blob = new Blob([lines], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${this.selectedEnvRepo.name}.env`
      a.click()
      URL.revokeObjectURL(url)
    },
  }
}
