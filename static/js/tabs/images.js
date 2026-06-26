export function imagesData() {
  return {
    images: [],

    async loadImages() {
      const r = await this.apiFetch('/api/images')
      if (r.ok) this.images = await r.json()
    },

    async runImage(img) {
      const r = await this.apiFetch(`/api/images/${img.id}/run`, { method: 'POST' })
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      this.currentTab = 'containers'
      await this.loadContainers()
    },

    async deleteImage(id) {
      if (!confirm(this.t('confirm_remove_image'))) return
      const r = await this.apiFetch(`/api/images/${id}`, { method: 'DELETE' })
      if (!r.ok) { const e = await r.json(); alert(e.detail); return }
      await this.loadImages()
    },
  }
}
