function app() {
  return {

    // ================================================================
    // i18n
    // ================================================================
    lang: 'zh',

    i18n: {
      zh: {
        tab_repos:            '仓库',
        tab_builds:           '构建历史',
        tab_images:           '镜像',
        tab_containers:       '容器',

        heading_repos:        '仓库列表',
        btn_add_repo:         '+ 添加仓库',
        form_new_repo:        '新增仓库',
        label_name:           '名称',
        label_source_type:    '来源类型',
        opt_remote:           '远端 (GitHub)',
        opt_local:            '本地 (已克隆)',
        label_github_url:     'GitHub 地址',
        label_local_path:     '本地路径',
        placeholder_name:     '项目名称',
        placeholder_local_path: '/home/user/projects/my-app',
        btn_save:             '保存',
        btn_cancel:           '取消',
        no_repos:             '暂无仓库，请点击右上角添加',
        btn_browse_commits:   '浏览提交',
        btn_delete:           '删除',

        heading_commits:      '提交记录',
        btn_refresh:          '刷新',
        loading_commits:      '加载中...',
        no_commits:           '暂无提交记录',
        btn_build:            '构建',

        heading_builds:       '构建历史',
        label_build:          '构建',
        no_builds:            '暂无构建记录',
        btn_logs:             '日志',
        btn_run:              '启动',
        run_success:          '容器已启动',

        status_pending:       '等待中',
        status_running:       '构建中',
        status_success:       '成功',
        status_failed:        '失败',

        heading_images:       'Docker 镜像',
        col_tags:             '标签',
        col_size:             '大小',
        col_created:          '创建时间',
        no_images:            '暂无镜像',
        btn_remove:           '删除',

        heading_containers:   '容器列表',
        col_name:             '名称',
        col_image:            '镜像',
        col_status:           '状态',
        no_containers:        '暂无容器',
        btn_start:            '启动',
        btn_stop:             '停止',
        btn_restart:          '重启',

        no_log:               '（无日志）',

        btn_env_vars:         '环境变量',
        heading_env_vars:     '环境变量',
        label_key:            '变量名',
        label_value:          '值',
        placeholder_key:      'MY_VAR',
        placeholder_value:    'my_value',
        btn_add:              '添加',
        no_env_vars:          '暂无环境变量',
        env_hint:             '构建时会写入 .env 文件并作为 --build-arg 传入',
        btn_paste_env:        '粘贴导入',
        btn_export_env:       '下载 .env',
        btn_import:           '解析导入',
        paste_placeholder:    '粘贴 .env 内容，例如：\nDB_HOST=localhost\nSECRET_KEY=abc123',
        import_success:       '已导入',
        import_unit:          '条',

        confirm_delete_repo:       '确定要删除该仓库吗？',
        confirm_remove_image:      '确定要删除该镜像吗？',
        confirm_remove_container:  '确定要删除该容器吗？',
        err_load_commits:          '加载提交记录失败',
        err_create_build:          '创建构建失败',
        err_save_repo:             '保存失败',
      },

      en: {
        tab_repos:            'Repositories',
        tab_builds:           'Builds',
        tab_images:           'Images',
        tab_containers:       'Containers',

        heading_repos:        'Repositories',
        btn_add_repo:         '+ Add Repository',
        form_new_repo:        'New Repository',
        label_name:           'Name',
        label_source_type:    'Source Type',
        opt_remote:           'Remote (GitHub)',
        opt_local:            'Local (already cloned)',
        label_github_url:     'GitHub URL',
        label_local_path:     'Local Path',
        placeholder_name:     'my-app',
        placeholder_local_path: '/home/user/projects/my-app',
        btn_save:             'Save',
        btn_cancel:           'Cancel',
        no_repos:             'No repositories yet. Add one above.',
        btn_browse_commits:   'Browse Commits',
        btn_delete:           'Delete',

        heading_commits:      'Commits',
        btn_refresh:          'Refresh',
        loading_commits:      'Loading commits...',
        no_commits:           'No commits found.',
        btn_build:            'Build',

        heading_builds:       'Build History',
        label_build:          'Build',
        no_builds:            'No builds yet.',
        btn_logs:             'Logs',
        btn_run:              'Run',
        run_success:          'Container started',

        status_pending:       'pending',
        status_running:       'running',
        status_success:       'success',
        status_failed:        'failed',

        heading_images:       'Docker Images',
        col_tags:             'Tags',
        col_size:             'Size',
        col_created:          'Created',
        no_images:            'No images found.',
        btn_remove:           'Remove',

        heading_containers:   'Containers',
        col_name:             'Name',
        col_image:            'Image',
        col_status:           'Status',
        no_containers:        'No containers found.',
        btn_start:            'Start',
        btn_stop:             'Stop',
        btn_restart:          'Restart',

        no_log:               '(no log)',

        btn_env_vars:         'Env Vars',
        heading_env_vars:     'Environment Variables',
        label_key:            'Key',
        label_value:          'Value',
        placeholder_key:      'MY_VAR',
        placeholder_value:    'my_value',
        btn_add:              'Add',
        no_env_vars:          'No environment variables yet.',
        env_hint:             'Injected as .env file and --build-arg during build',
        btn_paste_env:        'Paste Import',
        btn_export_env:       'Download .env',
        btn_import:           'Import',
        paste_placeholder:    'Paste .env content, e.g.:\nDB_HOST=localhost\nSECRET_KEY=abc123',
        import_success:       'Imported',
        import_unit:          'vars',

        confirm_delete_repo:       'Delete this repository?',
        confirm_remove_image:      'Remove this image?',
        confirm_remove_container:  'Remove this container?',
        err_load_commits:          'Failed to load commits',
        err_create_build:          'Failed to create build',
        err_save_repo:             'Failed to save repo',
      },
    },

    t(key) { return this.i18n[this.lang][key] ?? key },
    toggleLang() { this.lang = this.lang === 'zh' ? 'en' : 'zh' },

    // ================================================================
    // Auth
    // ================================================================
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

    // Unified fetch with auth header; auto-logout on 401
    async apiFetch(url, options = {}) {
      options.headers = { ...options.headers, 'X-Access-Token': this.token }
      const r = await fetch(url, options)
      if (r.status === 401) { this.logout(); return r }
      return r
    },

    // ================================================================
    // State
    // ================================================================
    tabs: [
      { id: 'repos' },
      { id: 'builds' },
      { id: 'images' },
      { id: 'containers' },
    ],
    currentTab: 'repos',

    // Repos
    repos: [],
    showAddRepo: false,
    newRepo: { name: '', source_type: 'remote', git_url: '', local_path: '' },
    formError: '',

    // Commits panel
    selectedRepo: null,
    commits: [],
    loadingCommits: false,

    // Env vars panel
    selectedEnvRepo: null,
    envVars: [],
    newEnvKey: '',
    newEnvVal: '',
    showPasteArea: false,
    pasteContent: '',
    importMsg: '',

    // Builds
    builds: [],
    activeBuild: null,
    buildLog: [],

    // Log modal
    logModal: null,

    // Images & Containers
    images: [],
    containers: [],

    // ================================================================
    // Init
    // ================================================================
    async init() {
      this._loadAuth()
      if (this.isAuthenticated) {
        await this.loadRepos()
      }
      this.$watch('currentTab', (tab) => {
        if (tab === 'builds')     this.loadBuilds()
        if (tab === 'images')     this.loadImages()
        if (tab === 'containers') this.loadContainers()
      })
    },

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
      if (!confirm(this.t('confirm_delete_repo'))) return
      await this.apiFetch(`/api/repos/${id}`, { method: 'DELETE' })
      if (this.selectedRepo?.id === id) { this.selectedRepo = null; this.commits = [] }
      await this.loadRepos()
    },

    // ================================================================
    // Commits
    // ================================================================
    async openRepo(repo) {
      this.selectedRepo = repo
      await this.loadCommits(repo)
    },

    async loadCommits(repo) {
      this.loadingCommits = true
      this.commits = []
      try {
        const r = await this.apiFetch(`/api/repos/${repo.id}/commits`)
        if (r.ok) this.commits = await r.json()
        else { const err = await r.json(); alert(err.detail || this.t('err_load_commits')) }
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
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      this.newEnvKey = ''; this.newEnvVal = ''
      await this.loadEnvVars(this.selectedEnvRepo)
    },

    async deleteEnvVar(env) {
      await this.apiFetch(`/api/repos/${this.selectedEnvRepo.id}/envs/${env.id}`, { method: 'DELETE' })
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
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
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

    // ================================================================
    // Builds
    // ================================================================
    async triggerBuild(repo, commit) {
      const r = await this.apiFetch('/api/builds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: repo.id, commit_sha: commit.sha, commit_message: commit.message }),
      })
      if (!r.ok) { alert(this.t('err_create_build')); return }
      const build = await r.json()
      this.currentTab = 'builds'
      this.activeBuild = build
      this.buildLog = []
      await this.streamBuild(build)
      await this.loadBuilds()
    },

    async streamBuild(build) {
      // EventSource doesn't support custom headers — pass token as query param
      const es = new EventSource(`/api/builds/${build.id}/stream?token=${encodeURIComponent(this.token)}`)
      es.onmessage = (e) => {
        const line = JSON.parse(e.data)
        this.buildLog.push(line)
        this.$nextTick(() => {
          const box = this.$refs.logBox
          if (box) box.scrollTop = box.scrollHeight
        })
        if (line === '[DONE] All done') {
          this.activeBuild = { ...this.activeBuild, status: 'success' }; es.close()
        } else if (line.startsWith('[ERROR]')) {
          this.activeBuild = { ...this.activeBuild, status: 'failed' }; es.close()
        }
      }
      es.onerror = () => es.close()
    },

    async loadBuilds() {
      const r = await this.apiFetch('/api/builds')
      if (r.ok) this.builds = await r.json()
    },

    showBuildLog(build) { this.logModal = build },

    async runBuild(build) {
      const r = await this.apiFetch(`/api/builds/${build.id}/run`, { method: 'POST' })
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      this.currentTab = 'containers'
      await this.loadContainers()
    },

    // ================================================================
    // Images
    // ================================================================
    async loadImages() {
      const r = await this.apiFetch('/api/images')
      if (r.ok) this.images = await r.json()
    },

    async deleteImage(id) {
      if (!confirm(this.t('confirm_remove_image'))) return
      const r = await this.apiFetch(`/api/images/${id}`, { method: 'DELETE' })
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      await this.loadImages()
    },

    // ================================================================
    // Containers
    // ================================================================
    async loadContainers() {
      const r = await this.apiFetch('/api/containers')
      if (r.ok) this.containers = await r.json()
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

    // ================================================================
    // Utils
    // ================================================================
    formatDate(iso) {
      if (!iso) return ''
      return new Date(iso).toLocaleString()
    },
  }
}
