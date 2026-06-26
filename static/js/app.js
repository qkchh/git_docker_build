import { i18nData }      from './i18n.js'
import { apiData }       from './api.js'
import { authData }      from './auth.js'
import { utilsData }     from './utils.js'
import { reposData }     from './tabs/repos.js'
import { buildsData }    from './tabs/builds.js'
import { imagesData }    from './tabs/images.js'
import { containersData } from './tabs/containers.js'

function navigationData() {
  return {
    tabs: [
      { id: 'repos' },
      { id: 'builds' },
      { id: 'images' },
      { id: 'containers' },
    ],
    currentTab: 'repos',
  }
}

function initData() {
  return {
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
  }
}

// Step 1 — register alpine:init listener BEFORE Alpine loads
document.addEventListener('alpine:init', () => {
  Alpine.data('app', () => ({
    ...i18nData(),
    ...apiData(),
    ...authData(),
    ...reposData(),
    ...buildsData(),
    ...imagesData(),
    ...containersData(),
    ...utilsData(),
    ...navigationData(),
    ...initData(),
  }))
})

// Step 2 — load all templates into DOM (top-level await, runs before Alpine)
async function loadTemplates() {
  const slots = document.querySelectorAll('[data-template]')
  await Promise.all([...slots].map(async (slot) => {
    const html = await fetch(slot.dataset.template).then(r => r.text())
    const tpl = document.createElement('template')
    tpl.innerHTML = html
    slot.replaceWith(tpl.content)
  }))
}

await loadTemplates()
document.body.style.visibility = ''

// Step 3 — inject Alpine CDN so it initializes on the complete DOM
const s = document.createElement('script')
s.defer = true
s.src = 'https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js'
document.head.appendChild(s)
